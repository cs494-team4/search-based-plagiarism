import astor
import ast

import utils as u
from .RefactorOperator import RefactorOperator

'''
Example:
a, b = True, True
if a or b:
    print(1)
    
-->
a, b = True, True
if a:
    print(1)
elif b:
    print(1)
'''


class SplitOrConditional(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = OrConditionalSplitter(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchSplitAbleIfOr()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return isinstance(node.test, ast.BoolOp) and isinstance(node.test.op, ast.Or)


class OrConditionalSplitter(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_If(self):
        if id(self.cur_node) == self.target \
                and SplitOrConditional.is_applicable(self.cur_node):
            self.applied = True

            parent_list = self.parent
            if_stmt = self.cur_node
            cur_index = parent_list.index(if_stmt)
            and_left = if_stmt.test.values[0]
            and_right = if_stmt.test.values[1]
            body_list = if_stmt.body
            orelse_list = if_stmt.orelse
            new_if = ast.If(and_left, body_list, [ast.If(and_right, body_list, [])])
            u.print_node(and_left)
            u.print_node(and_right)

            self.replace(new_if)


class SearchSplitAbleIfOr(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    # selects if statements that are structured like:
    # if A and B:
    def pre_If(self):
        if_stmt = self.cur_node
        cond_stmt = if_stmt.test
        if isinstance(cond_stmt, ast.BoolOp) and isinstance(cond_stmt.op, ast.Or):
            self.targets.append(id(if_stmt))
