import ast
import astor
import copy
from utils import print_node
from .RefactorOperator import RefactorOperator


class ExpandFunction(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = FunctionExpander(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchExpandableFunction()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return False


class FunctionExpander(astor.TreeWalk):
    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.definitions = []
        self.applied = False

    def pre_Call(self):
        node = self.cur_node
        if id(node) == self.target \
                and ExpandFunction.is_applicable(self.cur_node):
            self.applied = True
            parent = self.parent

            print(f'parent:{ast.dump(parent)}')

            fun_name = node.func.id
            fun_def = [func for func in self.definitions if func.name == fun_name][0]
            fun_body = fun_def.body
            fun_body_copy = copy.deepcopy(fun_body)

            fun_arg_names = [x.arg for x in fun_def.args.args]
            cal_arg_names = [x.id for x in node.args]

            var_replacement_dic = {fun_args: call_args for fun_args, call_args in zip(fun_arg_names, cal_arg_names)}
            replacer = VariableReplacer(var_replacement_dic)
            replacer.walk(fun_body_copy)

            self.replace(fun_body_copy)

    # search for a function definition
    def pre_FunctionDef(self):
        node = self.cur_node
        self.definitions.append(node)


class VariableReplacer(astor.TreeWalk):
    def __init__(self, mappings=dict()):
        astor.TreeWalk.__init__(self)
        self.mappings = mappings

    def pre_Name(self):
        node = self.cur_node
        n_id = node.id
        self.replace(ast.Name(id=self.mappings[n_id], ctx=ast.Load()))


class SearchExpandableFunction(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes
        self.definitions = []

    # only add functions that are defined in this st
    def pre_Call(self):
        parent = self.parent
        node = self.cur_node
        print_node(node)
        if node.func.id in self.definitions \
                and isinstance(parent, ast.Expr):
            self.targets.append(id(self.cur_node))

    # search for a function definition
    def pre_FunctionDef(self):
        node = self.cur_node
        self.definitions.append(node.name)
