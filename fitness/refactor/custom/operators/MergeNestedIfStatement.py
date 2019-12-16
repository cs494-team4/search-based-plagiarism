import ast

import astor

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

    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = NestedIfStatementMerger(target)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchMergeAbleNestedIfStatement()
        searcher.walk(codebase)
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
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
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
            results = list()
            if len(first_body[:second_index]) != 0:
                new_first_if = ast.If(first_test, first_body[:second_index], [])
                results.append(new_first_if)

            cur_index = self.parent.index(self.cur_node)
            # new_third_if = ast.If(first_test, second_else + first_body[second_index + 1:], first_else)
            first_and_op = ast.BoolOp(ast.And(), [first_test, second_test])
            second_and_op = ast.BoolOp(ast.And(), [first_test, ast.UnaryOp(ast.Not(), second_test)])

            if first_else or second_else:
                new_forth_if = ast.If(ast.UnaryOp(ast.Not(), first_test), first_else, [])
                if second_else:
                    new_third_if = ast.If(second_and_op, second_else, first_else)
                    new_second_if = ast.If(first_and_op, second_body, [new_third_if])
                else:
                    new_second_if = ast.If(first_and_op, second_body,
                                           [new_forth_if])
            else:
                new_second_if = ast.If(first_and_op, second_body, [])

            results.append(new_second_if)
            self.parent[cur_index:cur_index + 1] = results


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
