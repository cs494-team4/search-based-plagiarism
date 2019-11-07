import pytest
import moss


def test_moss():
    fitness = moss.get_score('samples/sample_original.py',
                             'samples/sample_refactored.py')

    assert fitness == 52
