import ast
import astor

from .RefactorOperator import RefactorOperator


class ForToWhile(RefactorOperator):

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        replacer = ReplaceForToWhile(target)
        #replacer.set_target(target)
        replacer.walk(self.codebase)
        return self.codebase, replacer.applied

    def search_targets(self):
        candidates = list()
        searcher = SearchRefactorablesForLoop()
        searcher.walk(self.codebase)
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
        if id(self.cur_node) == self.target \
                and ForToWhile.is_applicable(self.cur_node):

            # print("*** Refactor For => While: Node {}".format(self.target))
            # print("[Before Refactoring]")
            # print(astor.to_source(self.cur_node))

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

            # print("[After Refactoring]")
            # print_node(module_stmt)


class SearchRefactorablesForLoop(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)
        self.targets = []  # save parent nodes

    def pre_For(self):
        self.targets.append(id(self.cur_node))
