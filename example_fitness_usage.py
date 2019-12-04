from fitness.RefactorFitness import RefactorFitness

# initialization
"""fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='rope',
                      similarity_client='moss')"""

fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='moss')

# TODO Important: Find a robust representation (refactorings + TARGET)
refactorings = fit.available_refactorings

print('candidates: {}\n'.format(refactorings))

# repeated in the GA
sequences = list()  # List of refactorings produced by ga
sequences.append(refactorings[:1])
fitness_value = fit(sequences)[0]

print(fitness_value)
