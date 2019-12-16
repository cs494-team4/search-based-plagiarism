from fitness.RefactorFitness import RefactorFitness
from metaheuristics.FitnessOptimizerFactory import FitnessOptimizerFactory

fit = RefactorFitness(codebase='codebases/sample2/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='pycode')


refactorings = fit.available_refactorings
# print('candidates: {}\n'.format(refactorings))

fitness_optimizer = FitnessOptimizerFactory.create(
    "ga", refactorings, fit)


result_sequence = fitness_optimizer.get_best_individual()
print(result_sequence)
