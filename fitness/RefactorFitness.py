from fitness.similarity.SimilarityClientFactory import SimilarityClientFactory
from fitness.refactor.RefactorerFactory import RefactorerFactory

import copy


class RefactorFitness:

    def __init__(self,
                 codebase='codebases/sample2/sample_original.py',
                 refactorer_engine='rope',
                 similarity_client='pycode'):
        """
        :param codebase: path of codebase to apply refactorings to
        :param refactorer_engine: name of the refactoring framework to use
        :param similarity_client: name of the software similarity measurement to use
        """

        self.codebase = codebase
        self.refactor = RefactorerFactory.create(
            refactorer_engine, copy.deepcopy(codebase))
        self.similarity = SimilarityClientFactory.create(similarity_client)

        self.available_refactorings = self.refactor.refactorings

    def evaluate(self, sequences):
        # TODO add support for cache
        """
        :param sequences: list of candidates (represented by a list of refactorings) to be applied to the codebase
        :return: list of tuples (fitness value, boolean list that indicate application success for each refactorings)
                 of the corresponding candidates
        """

        refactored_codebases = list()
        success_indicators = list()
        for sequence in sequences:
            refactored_codebase, success_indcator = self.refactor(sequence)
            refactored_codebases.append(refactored_codebase)
            success_indicators.append(success_indcator)

        return [(score, success_indicators[i])
                for i, score in enumerate(self.similarity(self.codebase, refactored_codebases))]

    def __call__(self, *args, **kwargs):
        return self.evaluate(*args, **kwargs)
