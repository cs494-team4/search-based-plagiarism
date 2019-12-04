import abc


class RefactorOperator:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, target):
        """
        apply this refactoring to the target node and return self.codebase

        :param target: the id of the target object
        :return: the refactored codebase (self.codebase)
        """
        pass

    @abc.abstractmethod
    def search_targets(self):
        """
        find all targets (ast nodes) that this refactoring can be
        applied to and return a list of object identifiers (id(node))

        :return: a list of target object ids
        """
        pass

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []
