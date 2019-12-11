import astor
import ast

from utils import print_node
from .RefactorOperator import RefactorOperator


class PowToOperator(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = PowToOperatorReplacer(target)
        replacer.walk(self.codebase)
        return self.codebase

    def search_targets(self):
        candidates = list()
        searcher = SearchPow()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates


class PowToOperatorReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target

    def pre_Call(self):
        if id(self.cur_node) == self.target:
            self.replace(ast.BinOp(self.cur_node.args[0], ast.Pow(), self.cur_node.args[1]))


class SearchPow(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Call(self):
        call = self.cur_node
        if isinstance(call.func, ast.Name) and call.func.id == "pow":
            self.targets.append(id(self.cur_node))
