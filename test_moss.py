import pytest
import moss


def test_moss():
    fitness = moss.get_score('codebases/sample2/sample_original.py',
                             'codebases/sample2/sample_refactored.py')

    assert fitness == 52
