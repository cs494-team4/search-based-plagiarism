import ast
import random
import string
import astor

from .RefactorOperator import RefactorOperator


# TODO Test with complex compares
class CompToNaryFunc(RefactorOperator):
    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = CompToNaryFuncReplacer(target, codebase)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchComp()
        searcher.walk(codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return True


class CompToNaryFuncReplacer(astor.TreeWalk):

    def __init__(self, target, root):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.root = root
        self.applied = False

    def pre_Compare(self):
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
                and CompToNaryFunc.is_applicable(self.cur_node):
            self.applied = True

            # doesn't check for duplicate names atm
            fun_name = ''.join(random.choices(string.ascii_lowercase, k=10))

            fun_body = [ast.Return(self.cur_node)]

            walker = CompareWalker()
            walker.walk(fun_body[0])

            call = ast.Call(ast.Name(fun_name, ast.Store()), walker.args, [])
            fun = ast.FunctionDef(fun_name, ast.arguments(args=walker.arg_names, kwarg=None, vararg=None, defaults=[]),
                                  fun_body, [], None)

            # TODO: parent can be a return statement, can be Compare
            #  #see "TD example for return statement as parent for expression"
            insert_list = self.root.body
            for elem in insert_list:
                if not (isinstance(elem, ast.Import) or isinstance(elem, ast.ImportFrom)):
                    index = insert_list.index(elem)
                    insert_list.insert(index, fun)
                    break
            self.replace(call)



class CompareWalker(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.arg_names = list()
        self.index = 97
        self.args = list()

    def pre_Compare(self):

        if not isinstance(self.cur_node.left, ast.Compare):
            self.args.append(self.cur_node.left)
            self.cur_node.left = ast.Name(str(chr(self.index)), ast.Store())  # ast.Constant(self.index)
            self.arg_names.append(str(chr(self.index)))
            self.index += 1
        for i in range(len(self.cur_node.comparators)):
            if not isinstance(self.cur_node.comparators[i], ast.Compare):
                self.args.append(self.cur_node.comparators[i])
                self.cur_node.comparators[i] = ast.Name(str(chr(self.index)), ast.Store())  # ast.Constant(self.index)
                self.arg_names.append(str(chr(self.index)))
                self.index += 1


class SearchComp(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_Compare(self):
        if CompToNaryFunc.is_applicable(self.cur_node):
            self.targets.append(id(self.cur_node))
