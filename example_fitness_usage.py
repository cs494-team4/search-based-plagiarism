from fitness.RefactorFitness import RefactorFitness
from metaheuristics.FitnessOptimizerFactory import FitnessOptimizerFactory

fit = RefactorFitness(codebase='samples/sample_original.py',
                      refactorer_engine='custom',
                      similarity_client='moss')


refactorings = fit.available_refactorings
print('candidates: {}\n'.format(refactorings))

fitness_optimizer = FitnessOptimizerFactory.create(
    "ga", refactorings, fit)


result_sequence = fitness_optimizer.get_best_individual()
print(result_sequence)
