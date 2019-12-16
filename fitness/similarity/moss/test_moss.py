from fitness.similarity.moss.MossClient import MossClient


def test_moss():
    similarity = MossClient()
    fitness = similarity('codebases/sample2/sample_original.py',
                             'codebases/sample2/sample_refactored.py')

    assert fitness == 52
