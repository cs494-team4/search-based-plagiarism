from fitness.RefactorFitness import RefactorFitness

"""
Tests a given specified refactoring on a codebase.
The edited file will be stored in temp/
"""

# Path to the input codebase (singular python file at the moment)
file_path = "codebases/sample1/sample_original.py"

# Class name of the refactoring you want to test
refactoring_type = "ForToWhile"

# Index of target you want to apply the refactoring to
# -1 if you just want a display of the targets (to check if there are any)
target_index = 2


###################################################


fit = RefactorFitness(codebase=file_path,
                      refactorer_engine='custom',
                      similarity_client='test_dummy')

targets = fit.available_refactorings[refactoring_type]
print('targets: {}\n'.format(fit.available_refactorings))
print('targets: {}\n'.format(targets))

if target_index >= 0:
    sequences = list()
    sequences.append([(refactoring_type, targets[target_index])])
    fitness_value = fit(sequences)[0]


