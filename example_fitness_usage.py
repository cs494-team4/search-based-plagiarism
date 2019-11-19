from fitness.RefactorFitness import RefactorFitness

# initialization
"""fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='rope',
                      similarity_client='moss')"""

fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='test_dummy',
                      similarity_client='test_dummy')

refactorings = fit.available_refactorings  # TODO Important: Find a robust representation (refactorings + TARGET)


# repeated in the GA
sequences = list()  # List of refactorings produced by ga
sequences.append(list())
fitness_value = fit(sequences)[0]

print(fitness_value)

