import abc

"""
TODO

 - Support various lengths of sequence (but not too long)
 - Selection pressure for diversity in refactoring types
"""


class FitnessOptimizer(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, refactorings, fitness_func):
        elements = list()
        elements_map = dict()

        index = 0
        for r_type, targets in refactorings.items():
            targets_indexed = []
            if len(targets) == 0:
                continue

            for target in targets:
                elements.append((r_type, target))

                targets_indexed.append((target, index))
                index += 1

            elements_map[r_type] = targets_indexed

        self.elements_map = elements_map
        self.elements = elements

        self.fit = fitness_func
        # check if the number of possible elements is smaller than 5
        self.sequence_length = 10

    @abc.abstractmethod
    def get_best_individual(self):
        """
        finds a sequence of element with the best fitness value

        :return: list of possible elements subset
        """
        pass
