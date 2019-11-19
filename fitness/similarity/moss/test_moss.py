from fitness.similarity.moss.MossClient import MossClient


def test_moss():
    similarity = MossClient()
    fitness = similarity('samples/sample_original.py',
                             'samples/sample_refactored.py')

    assert fitness == 52
