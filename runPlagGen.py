from fitness.RefactorFitness import RefactorFitness
from metaheuristics.FitnessOptimizerFactory import FitnessOptimizerFactory

<<<<<<< HEAD:runPlagGen.py
fit = RefactorFitness(codebase='codebases/sample2/sample_original.py',  # Here, put your path to codebase to refactor.
=======
fit = RefactorFitness(codebase='codebases/sample1/_classical_simulator.py',
>>>>>>> Add scripts for plotting result on experiment:example_fitness_usage.py
                      refactorer_engine='custom',
                      similarity_client='moss')


refactorings = fit.available_refactorings
# print('candidates: {}\n'.format(refactorings))

fitness_optimizer = FitnessOptimizerFactory.create(
    "ga", refactorings, fit)


result_sequence = fitness_optimizer.get_best_individual()
print(result_sequence)
