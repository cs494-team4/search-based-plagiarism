import ast

import astor

from .RefactorOperator import RefactorOperator


class ForToWhile(RefactorOperator):

    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        replacer = ReplaceForToWhile(target)
        # replacer.set_target(target)
        replacer.walk(codebase)
        return codebase, replacer.applied

    def search_targets(self, codebase):
        candidates = list()
        searcher = SearchRefactorablesForLoop()
        searcher.walk(codebase)
        candidates.extend(
            [target for target in searcher.targets])
        return candidates

    @staticmethod
    def is_applicable(node):
        return True


class ReplaceForToWhile(astor.TreeWalk):

    def __init__(self, target):
        astor.TreeWalk.__init__(self)
        self.target = target
        self.applied = False

    def pre_For(self):
        if hasattr(self.cur_node, 'custom_id') \
                and self.cur_node.custom_id == self.target \
                and ForToWhile.is_applicable(self.cur_node):
            self.applied = True
            _target = astor.to_source(self.cur_node.target).strip()
            _iter = astor.to_source(self.cur_node.iter).strip()
            body = self.cur_node.body

            module_stmt = ast.parse("i=0\nwhile i<len({}): i+=1".format(_iter))
            while_stmt = module_stmt.body[1]

            body.insert(0, ast.parse("{}={}[i]".format(_target, _iter)))
            body.append(ast.parse("i+=1"))
            while_stmt.body = body
            while_stmt.orelse = self.cur_node.orelse
            self.replace(module_stmt)


class SearchRefactorablesForLoop(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_For(self):
        self.targets.append(id(self.cur_node))
