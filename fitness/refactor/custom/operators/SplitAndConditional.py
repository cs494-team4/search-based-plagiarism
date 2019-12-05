import astor
import ast

from utils import print_node
from .RefactorOperator import RefactorOperator


class SplitAndConditional(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = AndConditionalSplitter(target)
        replacer.walk(self.codebase)
        return self.codebase

    def search_targets(self):
        candidates = list()
        searcher = SearchSplitAbleIfAnd()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates


class AndConditionalSplitter(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target

    def pre_If(self):
        if id(self.cur_node) == self.target:
            parent_list = self.parent
            and_left = self.cur_node.test.values[0]
            and_right = self.cur_node.test.values[1]
            body_list = self.cur_node.body
            orelse_list = self.cur_node.orelse

            new_upper_if = ast.If()
            new_lower_if = ast.If()
            new_else_if = ast.If()

            new_upper_if.test = and_left
            new_upper_if.body = [new_lower_if]
            new_upper_if.orelse = []

            new_lower_if.test = and_right
            new_lower_if.body = body_list
            new_lower_if.orelse = []

            if len(orelse_list) > 0:
                new_else_if.test = ast.UnaryOp(ast.Not(), self.cur_node.test)
                new_else_if.body = orelse_list
                new_else_if.orelse = []
                index = parent_list.index(self.cur_node)
                parent_list[index: index + 1] = [new_upper_if, new_else_if]
            else:
                self.replace(new_upper_if)


class SearchSplitAbleIfAnd(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    # selects if statements that are structured like:
    # if A and B:
    def pre_If(self):
        if_stmt = self.cur_node
        cond_stmt = if_stmt.test
        if isinstance(cond_stmt, ast.BoolOp) and isinstance(cond_stmt.op, ast.And):
            self.targets.append(id(if_stmt))
