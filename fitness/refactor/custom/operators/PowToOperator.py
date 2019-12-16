import astor
import ast

from .RefactorOperator import RefactorOperator


class PowToOperator(RefactorOperator):
    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = PowToOperatorReplacer(target)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchPow()
        searcher.walk(codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return isinstance(node.func, ast.Name) and node.func.id == "pow"


class PowToOperatorReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_Call(self):
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
                and PowToOperator.is_applicable(self.cur_node):
            self.applied = True
            self.replace(ast.BinOp(self.cur_node.args[0], ast.Pow(), self.cur_node.args[1]))


class SearchPow(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Call(self):
        if PowToOperator.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))
