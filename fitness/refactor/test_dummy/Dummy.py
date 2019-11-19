from fitness.refactor.Refactorer import Refactorer


class Dummy(Refactorer):

    def parse_codebase(self, codebase, *args, **kwargs):
        return codebase  # No internal representation for the dummy

    def retrieve_refactorings(self):
        return list()

    def apply(self, sequence, *args, **kwargs):
        return self.codebase_repr
