import astor
import ast

from utils import print_node
from .RefactorOperator import RefactorOperator


class OperatorToPow(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = OperatorToPowReplacer(target)
        replacer.walk(self.codebase)
        return self.codebase

    def search_targets(self):
        candidates = list()
        searcher = SearchPowOp()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates


class OperatorToPowReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target

    def pre_BinOp(self):
        if id(self.cur_node) == self.target:
            self.replace(ast.Call(ast.Name("pow",ast.Store()), [self.cur_node.left, self.cur_node.right], []))


class SearchPowOp(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_BinOp(self):
        if isinstance(self.cur_node.op, ast.Pow):
            self.targets.append(id(self.cur_node))
