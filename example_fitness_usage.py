from fitness.RefactorFitness import RefactorFitness

# initialization
fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='pycode')


refactorings = fit.available_refactorings
print('candidates: {}\n'.format(refactorings))

# repeated in the GA

sequence = list()
for refactoring_type, targets in refactorings.items():
    target = targets[0]
    sequence.append((refactoring_type, target))

print(sequence)

fitness_value = fit([sequence[:1]])[0]

print(fitness_value)
