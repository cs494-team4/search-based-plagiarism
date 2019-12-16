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
            cur_index = self.parent.index(self.cur_node)

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

            if first_body[:second_index]:
                results.append(ast.If(first_test, first_body[:second_index], []))

            if second_body:
                a_and_b = ast.BoolOp(ast.And(), [first_test, second_test])
                if_a_and_b = ast.If(a_and_b, second_body, [])
                results.append(if_a_and_b)
                if second_else:
                    a_and_not_b = ast.BoolOp(ast.And(), [first_test, ast.UnaryOp(ast.Not(), second_test)])
                    if_a_and_not_b = ast.If(a_and_not_b, second_else, [])
                    if_a_and_b.orelse = [if_a_and_not_b]
            if first_body[second_index + 1:]:
                results.append(ast.If(first_test, first_body[second_index + 1:], first_else))
            elif first_else:
                results.append(ast.If(ast.UnaryOp(ast.Not(), first_test), first_else, []))
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
