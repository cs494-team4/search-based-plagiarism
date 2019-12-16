from .RefactorOperator import RefactorOperator


class Identity(RefactorOperator):
    def __init__(self):
        self.targets = []

    def apply(self, codebase, target):
        return codebase, True

    def search_targets(self, codebase):
        return [id(codebase)]

    @staticmethod
    def is_applicable(node):
        return True
