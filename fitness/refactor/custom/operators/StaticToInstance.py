# Reference:
# https://julien.danjou.info/python-ast-checking-method-declaration/

import ast
import astor

from utils import print_node
from .RefactorOperator import RefactorOperator

class StaticToInstance(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = ChangeStaticToInstance(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchRefactorableStatic()
        searcher.walk(self.codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates
    
    @staticmethod
    def is_applicable(node):
        return any(isinstance(node, ast.FunctionDef) for node in node.body)

class ChangeStaticToInstance(astor.TreeWalk):
    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False
    
    # TODO: change Class.static_method() usage as self.instance_method() usage also, if any
    def pre_FunctionDef(self):  # TODO: check FunctionDef or ClassDef?
        if id(self.cur_node) == self.target \
            and StaticToInstance.is_applicable(self.cur_node):
            self.applied = True
            curr_node = self.cur_node
            # insert keyword SELF in FunctionDef
            curr_node.args.args.insert(0, ast.arg(arg='self', annotation=None))
            # remove @staticmethod decorator in decorator_list
            curr_node.decorator_list = [d for d in self.cur_node.decorator_list \
                                            if not (isinstance(d, ast.Name) and d.id == 'staticmethod')]
            # print_node(curr_node)
            self.replace(curr_node)

class SearchRefactorableStatic(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []   # save refactorable functions

    def pre_ClassDef(self):
        class_stmt = self.cur_node
        # If it's a class, iterate over its body member to find static methods
        for body_item in class_stmt.body:
            # Not a method, skip
            if not isinstance(body_item, ast.FunctionDef):
                continue
            # Check that it has a decorator
            for decorator in body_item.decorator_list:
                if (isinstance(decorator, ast.Name)
                    and decorator.id == 'staticmethod'):
                    # It's a static function
                    self.targets.append(id(body_item))


            