from metaheuristics.FitnessOptimizer import FitnessOptimizer

import random

from deap import base
from deap import creator
from deap import tools


class GAOptimizer(FitnessOptimizer):
    def __init__(self, possible_elements, fitness_func):
        super().__init__(possible_elements, fitness_func)

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        toolbox = base.Toolbox()
        toolbox.register("indices", random.sample,
                         range(len(self.elements)), self.sequence_length)

        toolbox.register("individual", tools.initIterate,
                         creator.Individual, toolbox.indices)
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)

        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", self.evaluate)

        self.toolbox = toolbox

    def evaluate(self, individual):
        sequence = []
        for index in individual:
            sequence.append(self.elements[index])

        fit = self.fit([sequence])[0]
        return (float(fit), )

    def get_best_individual(self):
        pop = self.evolve_population()
        fitnesses = map(self.toolbox.evaluate, pop)

        best_fit = 10**10
        best_ind = None
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            if fit[0] < best_fit:
                best_fit = fit[0]
                best_ind = ind

        print('best fitness: {}'.format(best_fit))
        return [self.elements[index] for index in best_ind]

    def evolve_population(self, n=3, CXPB=0.5, MUTPB=0.2, NGEN=5):
        toolbox = self.toolbox

        pop = toolbox.population(n)
        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        for g in range(NGEN):
            average_fitness = sum(
                map(lambda x: self.toolbox.evaluate(x)[0], pop))/len(pop)
            print('{}th generation: {}'.format(g, average_fitness))

            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            pop[:] = offspring

        return pop
