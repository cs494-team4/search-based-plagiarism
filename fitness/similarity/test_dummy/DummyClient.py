from fitness.similarity.SimilarityClient import SimilarityClient


class DummyClient(SimilarityClient):

    def get_scores(self, original_code, refactored_codebases):
        return [100]

    def retrieve_refactorings(self):
        return list()

