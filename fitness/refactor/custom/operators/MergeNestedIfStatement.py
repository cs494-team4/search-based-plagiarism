import astor
import ast
from .RefactorOperator import RefactorOperator

'''
Example:
a,b = True, True
if a:
    if b:
        print(1)
-->
if a and b:
    print(1)  

'''


class MergeNestedIfStatement(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = NestedIfStatementMerger(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchMergeAbleNestedIfStatement()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return any(isinstance(node, ast.If) for node in node.body)


class NestedIfStatementMerger(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_If(self):
        if id(self.cur_node) == self.target \
                and MergeNestedIfStatement.is_applicable(self.cur_node):
            self.applied = True
            parent_list = self.parent

            first_if = self.cur_node
            first_test = first_if.test
            first_body = first_if.body
            first_else = first_if.orelse

            second_if = [node for node in first_body if isinstance(node, ast.If)][0]
            second_index = first_body.index(second_if)
            second_test = second_if.test
            second_body = second_if.body
            second_else = second_if.orelse
            new_first_if = ast.If(first_test, first_body[:second_index], first_else)
            cur_index = self.parent.index(self.cur_node)
            new_third_if = ast.If(first_test, second_else + first_body[second_index + 1:], [])
            and_op = ast.BoolOp(ast.And(), [first_test, second_test])
            new_second_if = ast.If(and_op, second_body, [new_third_if])
            self.parent[cur_index:cur_index + 1] = [new_first_if, new_second_if]


class SearchMergeAbleNestedIfStatement(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    # selects if statements that are structured like:
    # if A and B:
    def pre_If(self):
        if_stmt = self.cur_node
        body = if_stmt.body

        if any(isinstance(node, ast.If) for node in body):
            self.targets.append(id(if_stmt))
