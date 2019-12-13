from .RefactorOperator import RefactorOperator


class Identity(RefactorOperator):
    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []

    def apply(self, target):
        return self.codebase, True

    def search_targets(self):
        return [id(self.codebase)]

    @staticmethod
    def is_applicable(node):
        return True
