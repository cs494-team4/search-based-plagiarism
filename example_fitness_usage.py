from fitness.RefactorFitness import RefactorFitness

# initialization
fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='moss')


refactorings = fit.available_refactorings
print('candidates: {}\n'.format(refactorings))

refactoring_type = list(refactorings.keys())[0]
target = refactorings[refactoring_type][0]


# repeated in the GA
sequences = list()

sequence = list()
sequence.append((refactoring_type, target))

sequences.append(sequence)

fitness_value = fit(sequences)[0]

print(fitness_value)
