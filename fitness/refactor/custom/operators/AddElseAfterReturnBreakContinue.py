import astor
import ast

from .RefactorOperator import RefactorOperator


class AddElseAfterReturnBreakContinue(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = OrConditionalSplitter(target)
        replacer.walk(self.codebase)
        return self.codebase

    def search_targets(self):
        candidates = list()
        searcher = SearchSplitAbleIfOr()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates


class OrConditionalSplitter(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target

    def pre_If(self):
        if id(self.cur_node) == self.target:
            curr_node = self.cur_node
            cur_index = self.parent.index(curr_node)
            parents = self.parent
            after_if = parents[cur_index + 1:]
            new_if = ast.If(curr_node.test, curr_node.body, after_if)
            parents[cur_index:] = [new_if]


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
