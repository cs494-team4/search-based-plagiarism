import astor
import ast

from utils import print_node
from .RefactorOperator import RefactorOperator


# TODO Implement the thing
class StringConcatToFormat(RefactorOperator):
    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = StringConcatToFormatReplacer(target)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchStringConcat()
        searcher.walk(codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return True


class StringConcatToFormatReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_BinOp(self):
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
                and StringConcatToFormat.is_applicable(self.cur_node):
            self.applied = True
            self.cur_node.left
            self.cur_node.right
            self.replace(ast.Call(ast.Name("pow", ast.Store()), [self.cur_node.left, self.cur_node.right], []))
            # Call(func=Attribute(value=Str(s='test1 {} test2 {}'), attr='format', ctx=Load()), args=[Num(n=1), Num(n=3)], keywords=[])



class SearchStringConcat(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_BinOp(self):
        if StringConcatToFormat.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))
