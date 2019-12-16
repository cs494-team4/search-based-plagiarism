import abc


class RefactorOperator:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def apply(self, codebase, target):
        """
        apply this refactoring to the target node and return the codebase
        and an indicator if the application was successful

        :param codebase: the ast to apply the refactoring to
        :param target: the id of the target object
        :return: Tuple : (the refactored codebase (self.codebase) , boolean if the application was successful)
        """
        pass

    @abc.abstractmethod
    def search_targets(self, codebase):
        """
        find all targets (ast nodes) that this refactoring can be
        applied to  and return a list of object identifiers (id(node))

        :param codebase: the ast to search for refactorings
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

    def __init__(self):
        self.targets = []
