import ast

import astor

from .RefactorOperator import RefactorOperator

'''
a = True
for elem in range(5):
    if a:
        continue
    print(1)
        

-->
for elem in range(5):
    if a:
        break
    else:
        print(1)
'''


class AddElseAfterReturnBreakContinue(RefactorOperator):

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
        return (isinstance(node.body[-1], ast.Return)
                or isinstance(node.body[-1], ast.Break)
                or isinstance(node.body[-1], ast.Continue)) \
               and len(node.orelse) == 0


class OrConditionalSplitter(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_If(self):
        if id(self.cur_node) == self.target \
                and AddElseAfterReturnBreakContinue.is_applicable(self.cur_node):
            self.applied = True
            curr_node = self.cur_node
            cur_index = self.parent.index(curr_node)
            parents = self.parent
            after_if = parents[cur_index + 1:]
            curr_node.orelse = after_if

            parents[cur_index:] = [curr_node]


class SearchSplitAbleIfOr(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_If(self):
        if_stmt = self.cur_node
        if (isinstance(if_stmt.body[-1], ast.Return)
            or isinstance(if_stmt.body[-1], ast.Break)
            or isinstance(if_stmt.body[-1], ast.Continue)) \
                and len(if_stmt.orelse) < 1:
            self.targets.append(id(if_stmt))
