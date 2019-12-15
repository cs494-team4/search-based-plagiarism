import astor
import ast
from string import Formatter

from .RefactorOperator import RefactorOperator


# currently only supporting default argument formatstring ({} but not {name} )

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
        if not( isinstance(node.func, ast.Attribute) \
                    and node.func.attr == 'format' \
                    and isinstance(node.func.value, ast.Str)):
            return False

        string = node.func.value.s
        for i in range(len(string)):
            if string[i] == "{":
                if i == (len(string)-1) or string[i+1] != "}":
                    return False

        return True


class FormatToStringConcatReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

        self.values = list()

    def pre_Call(self):
        if id(self.cur_node) == self.target and FormatToStringConcat.is_applicable(self.cur_node):
            self.applied = True

            fragments = [x for x in Formatter().parse(self.cur_node.func.value.s)]

            if len(fragments) == 0 or len(self.cur_node.args) == 0:
                return

            for arg in self.cur_node.args:
                if isinstance(arg, ast.Str):
                    self.values.append(arg)
                else:
                    self.values.append(ast.Call(ast.Name("str", ast.Store()), [arg], []))

            string, _, _, _ = fragments.pop(0)
            if string == "":
                expr = self.values.pop(0)
            else:
                expr = ast.BinOp(ast.Str(string), ast.Add(), self.values.pop(0))

            for frag in fragments:
                string, _, spec, _ = frag
                if spec is None:
                    break
                expr = ast.BinOp(expr, ast.Add(), ast.Str(string))
                expr = ast.BinOp(expr, ast.Add(), self.values.pop(0))

            self.replace(expr)


class SearchFormatString(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Call(self):  # is applicable
        if FormatToStringConcat.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))

