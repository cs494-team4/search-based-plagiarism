import abc


class SimilarityClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_scores(self, original_code, refactored_codebases):
        """

        :param original_code: base code to compare the refactored versions to
        :param refactored_codebases: list of refactored code bases to compare with the base
        :return: list of similarity scores for each refactored codebase
        """
        pass

    def __call__(self, *args, **kwargs):
        return self.get_scores(*args, **kwargs)
