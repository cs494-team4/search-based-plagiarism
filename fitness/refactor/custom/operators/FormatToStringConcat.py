import astor
import ast

from utils import print_node
from .RefactorOperator import RefactorOperator


class FormatToStringConcat(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target): # return success
        replacer = FormatToStringConcatReplacer(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchFormatString()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return isinstance(node.func, ast.Attribute) \
                    and node.func.attr == 'format' \
                    and isinstance(node.func.value, ast.Str)


class FormatToStringConcatReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_Call(self):
        if id(self.cur_node) == self.target and FormatToStringConcat.is_applicable(self.cur_node):
            self.applied = True
            call = ast.Call(ast.Name("str", ast.Store()), [STRING_ARGS], [])

            # Call(func=Attribute(value=Str(s='test1 {} test2 {}'), attr='format', ctx=Load()), args=[Num(n=1), Num(n=3)], keywords=[])


class SearchFormatString(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Call(self):  # is applicable
        if FormatToStringConcat.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))

