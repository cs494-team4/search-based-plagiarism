from fitness.RefactorFitness import RefactorFitness

# initialization
fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='moss')


refactorings = fit.available_refactorings

refactoring_type = refactorings.keys()[0]
target = refactorings[refactoring_type][0]

print('candidates: {}\n'.format(refactorings))

# repeated in the GA
sequences = list()
sequences.append((refactoring_type, target))

fitness_value = fit(sequences)[0]

print(fitness_value)
