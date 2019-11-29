from fitness.refactor.Refactorer import Refactorer

import astor

# TODO custom refactorer
# for to while / while to for

refactoring_types = [
    'ForToWhile',
    'WhileToFor'
]


class SearchRefactorables_ForLoop(astor.TreeWalk):
    def __init__(self):
        astor.TreeWalk.__init__(self)

        self.targets = []   # save parent nodes

    def pre_For(self):
        print(self.cur_node)
        self.targets.append(self.parent)


class RefactorOperation():
    # refactoring: defined by (type, target)

    def __init__(self, refactor_type, target):
        self.refactor_type = refactor_type
        self.target = target


class CustomRefactorer(Refactorer):
    def parse_codebase(self, codebase, *args, **kwargs):
        return astor.parse_file(codebase)

    def retrieve_refactorings(self):
        # For now, just assume that all possible refactorings can be applicable to any codebases
        return refactoring_types

    def apply(self, sequence, *args, **kwargs):
        return self.codebase_repr
