import astor
import ast
import random
import string

from utils import print_node
from .RefactorOperator import RefactorOperator


# TODO test the thing
class ExprToNaryFunc(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = ExprToNaryFuncReplacer(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchBinExpr()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return True


class ExprToNaryFuncReplacer(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_BinOp(self):
        if id(self.cur_node) == self.target and ExprToNaryFunc.is_applicable(self.cur_node):
            self.applied = True

            # doesn't check for duplicate names atm
            fun_name = ''.join(random.choices(string.ascii_lowercase, k=10))

            fun_body = [ast.Return(self.cur_node)]

            walker = BinaryWalker()
            walker.walk(fun_body[0])

            call = ast.Call(ast.Name(fun_name, ast.Store()), walker.args, [])
            fun = ast.FunctionDef(fun_name, ast.arguments(args=walker.arg_names,kwarg=None,vararg=None, defaults=[]), fun_body , [], None)

            self.replace(call)
            self.parent.insert(0, fun)


class BinaryWalker(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.arg_names = list()
        self.index = 97
        self.args = list()

    def pre_BinOp(self):

        if not isinstance(self.cur_node.left, ast.BinOp):
            self.args.append(self.cur_node.left)
            self.cur_node.left = ast.Name(str(chr(self.index)),ast.Store()) #ast.Constant(self.index)
            self.arg_names.append(str(chr(self.index)))
            self.index += 1
        if not isinstance(self.cur_node.right, ast.BinOp):
            self.args.append(self.cur_node.right)
            self.cur_node.right = ast.Name(str(chr(self.index)),ast.Store()) #ast.Constant(self.index)
            self.arg_names.append(str(chr(self.index)))
            self.index += 1



class SearchBinExpr(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_BinOp(self):
        if ExprToNaryFunc.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))
