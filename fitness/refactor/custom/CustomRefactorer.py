from fitness.refactor.Refactorer import Refactorer

import abc
import astor
import ast

# [In Progress] custom refactorer
# method-level refactoring operators

refactor_types = [
    'ForToWhile'
]

refactored_files_path = 'temp/'


def print_node(node):
    print(astor.to_source(node))


class SearchRefactorables_ForLoop(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)

        self.targets = []   # save parent nodes

    def pre_For(self):
        self.targets.append(id(self.cur_node))


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

            # print_node(module_stmt)
            self.replace(module_stmt)

            # after
            print("[After Refactoring]")
            print_node(module_stmt)


class RefactorOperation():
    # refactoring: defined by (type, target)
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply_to_codebase(self, codebase):
        pass

    def __init__(self, target):
        self.target = target

    def __repr__(self):
        return str(self.target)


class ForToWhile(RefactorOperation):
    __metaclass__ = abc.ABCMeta

    def apply_to_codebase(self, codebase):
        replacer = ReplaceForToWhile()
        replacer.set_target(self.target)
        replacer.walk(codebase)

        return codebase

    def __repr__(self):
        return 'ForToWhile(target:{})'.format(str(self.target))


class CustomRefactorer(Refactorer):
    def parse_codebase(self, codebase, *args, **kwargs):
        return astor.parse_file(codebase)

    def retrieve_refactorings(self):
        # For now, just assume that all possible refactorings can be applicable to any codebases
        refactor_candidates = []

        for refactor_type in refactor_types:
            if refactor_type == 'ForToWhile':
                searcher = SearchRefactorables_ForLoop()
                searcher.walk(self.codebase_repr)
                refactor_candidates.extend(
                    [ForToWhile(target) for target in searcher.targets])

            elif refactor_type == 'WhileToFor':
                pass

            # TODO: more diverse refactoring types

        return refactor_candidates

    def apply(self, sequence, *args, **kwargs):
        codebase = self.codebase_repr

        for op in sequence:
            codebase = op.apply_to_codebase(codebase)

        filename = '{}{}.py'.format(refactored_files_path, id(codebase))
        with open(filename, 'w') as f:
            f.write(astor.to_source(codebase))

        return filename
