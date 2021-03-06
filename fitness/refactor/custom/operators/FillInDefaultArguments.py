import astor
import ast
import utils as u
from .RefactorOperator import RefactorOperator


class FillInDefaultArguments(RefactorOperator):

    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = DefaultArgumentsFiller(target)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchFillInFDefaultArguments()
        searcher.walk(codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    # todo: rethink is_applicable
    @staticmethod
    def is_applicable(input1):
        node, fun_def = input1

        return fun_def is not None and len(node.args) + len(node.keywords) < len(fun_def.args.defaults)


class DefaultArgumentsFiller(astor.TreeWalk):
    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.fun_defs = []
        self.applied = False

    def pre_Call(self):
        node = self.cur_node
        fun_def = next(x for x in self.fun_defs if x.name == node.func.id)
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
                and FillInDefaultArguments.is_applicable((node, fun_def)):
            self.applied = True
            node = self.cur_node
            fun_args_args = fun_def.args.args
            fun_defaults = fun_def.args.defaults
            call_args = node.args
            call_keywords = node.keywords

            filled_index = len(call_args)
            left_over_args = fun_args_args[filled_index:]
            left_over_defaults = fun_defaults[filled_index:]

            call_keywords_args = [x.arg for x in call_keywords]
            for i, a in enumerate(left_over_args):
                if a.arg not in call_keywords_args:
                    call_keywords.append(ast.keyword(arg=a.arg, value=left_over_defaults[i]))

    # search for a function definition
    def pre_FunctionDef(self):
        node = self.cur_node
        if node.args.defaults:
            self.fun_defs.append(node)


class SearchFillInFDefaultArguments(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes
        self.fun_defs = []

    def pre_Call(self):
        node = self.cur_node
        if isinstance(node.func, ast.Name):
            fun_def = next((x for x in self.fun_defs if x.name == node.func.id), None)
            if fun_def is not None \
                    and len(node.args) + len(node.keywords) < len(fun_def.args.defaults):
                self.targets.append(id(node))

    # search for a function definition
    def pre_FunctionDef(self):
        node = self.cur_node
        if node.args.defaults:
            self.fun_defs.append(node)
