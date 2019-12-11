import abc


class RefactorOperator:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, target):
        """
        apply this refactoring to the target node and return self.codebase
        and an indicator if the application was successful

        :param target: the id of the target object
        :return: Tuple : (the refactored codebase (self.codebase) , boolean if the application was successful)
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

    @staticmethod
    @abc.abstractmethod
    def is_applicable(node):
        """
        check if the refactoring is applicable to a given node

        :param node: the node to be checked
        :return: a boolean indicating if the application is possible
        """

        pass

    def __init__(self, codebase):
        self.codebase = codebase
        self.targets = []
