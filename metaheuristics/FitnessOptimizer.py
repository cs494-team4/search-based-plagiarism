import abc

"""
TODO

 - Support various lengths of sequence (but not too long)
 - Selection pressure for diversity in refactoring types
"""


class FitnessOptimizer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, elements, fitness_func):
        self.elements = elements
        self.fit = fitness_func
        self.sequence_length = 5    # check if the number of possible elements is smaller than 5

    @abc.abstractmethod
    def get_best_individual(self):
        """
        finds a sequence of element with the best fitness value

        :return: list of possible elements subset
        """
        pass
