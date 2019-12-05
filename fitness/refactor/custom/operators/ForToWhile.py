import abc
import ast
import astor

from utils import print_node
from .RefactorOperator import RefactorOperator


class ForToWhile(RefactorOperator):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, target):
        replacer = ReplaceForToWhile()
        replacer.set_target(target)
        replacer.walk(self.codebase)
        return self.codebase

    @abc.abstractmethod
    def search_targets(self):
        candidates = list()
        searcher = SearchRefactorablesForLoop()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])

        return candidates


class ReplaceForToWhile(astor.TreeWalk):
    def set_target(self, target):
        self.target = target

    def pre_For(self):
        if id(self.cur_node) == self.target:
            print("*** Refactor For => While: Node {}".format(self.target))
            # before
            print("[Before Refactoring]")
            print(astor.to_source(self.cur_node))

            _target = astor.to_source(self.cur_node.target).strip()
            _iter = astor.to_source(self.cur_node.iter).strip()
            body = self.cur_node.body

            module_stmt = ast.parse("i=0\nwhile i<len({}): i+=1".format(_iter))
            while_stmt = module_stmt.body[1]

            body.insert(0, ast.parse("{}={}[i]".format(_target, _iter)))
            body.append(ast.parse("i+=1"))

            while_stmt.body = body
            while_stmt.orelse = self.cur_node.orelse

            print_node(module_stmt)
            self.replace(module_stmt)

            # after
            print("[After Refactoring]")
            print_node(module_stmt)


class SearchRefactorablesForLoop(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []   # save parent nodes

    def pre_For(self):
        self.targets.append(id(self.cur_node))
