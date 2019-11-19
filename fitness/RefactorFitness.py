from fitness.similarity.SimilarityClientFactory import SimilarityClientFactory
from fitness.refactor.RefactorerFactory import RefactorerFactory


class RefactorFitness:

    def __init__(self,
                 codebase='sample1/sample_original.py',
                 refactorer_engine='rope',
                 similarity_client='moss'):
        """
        :param codebase: path of codebase to apply refactorings to
        :param refactorer_engine: name of the refactoring framework to use
        :param similarity_client: name of the software similarity measurement to use
        """

        self.codebase = codebase
        self.refactor = RefactorerFactory.create(refactorer_engine, codebase)
        self.similarity = SimilarityClientFactory.create(similarity_client)

        self.available_refactorings = self.refactor.refactorings

    def evaluate(self, sequences):
        # TODO add support for cache

        """
        :param sequences: list of candidates (represented by a list of refactorings) to be applied to the codebase
        :return: list of fitness values of the corresponding candidates
        """

        refactored_codebases = list()
        for sequence in sequences:
            refactored_codebases.append(self.refactor(sequence))

        return self.similarity(self.codebase, refactored_codebases)

    def __call__(self, *args, **kwargs):
        return self.evaluate(*args, **kwargs)
