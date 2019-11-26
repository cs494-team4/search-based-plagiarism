from fitness.similarity.moss.MossClient import MossClient
from fitness.similarity.test_dummy.DummyClient import DummyClient


class SimilarityClientFactory:

    __similarity_classes = {
        "moss": MossClient,
        "test_dummy": DummyClient
    }

    @staticmethod
    def create(name, *args, **kwargs):
        similarity_class = SimilarityClientFactory.__similarity_classes.get(name.lower(), None)

        if similarity_class:
            return similarity_class(*args, **kwargs)
        raise NotImplementedError("The similarity "+str(name)+" is not implemented")
