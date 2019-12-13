from fitness.RefactorFitness import RefactorFitness
from metaheuristics.FitnessOptimizerFactory import FitnessOptimizerFactory

fit = RefactorFitness(codebase='codebases/sample1/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='moss')


refactorings = fit.available_refactorings
print('candidates: {}\n'.format(refactorings))

possible_refactorings = list()
for refactoring_type, targets in refactorings.items():
    for target in targets:
        possible_refactorings.append((refactoring_type, target))

    break   # remove if a bug in conditional refactoring operator is fixed

print(possible_refactorings)

fitness_optimizer = FitnessOptimizerFactory.create(
    "ga", possible_refactorings, fit)


result_sequence = fitness_optimizer.get_best_individual()
print(result_sequence)
