import random

from deap import base
from deap import creator
from deap import tools

from metaheuristics.FitnessOptimizer import FitnessOptimizer
from utils import OrderedSet


def pick_index_biased(elements_map):
    r_types = elements_map.keys()

    type_index = random.randrange(len(r_types))
    r_type = list(r_types)[type_index]
    target_index = random.randrange(len(elements_map[r_type]))

    return elements_map[r_type][target_index][1]


class GAOptimizer(FitnessOptimizer):
    def __init__(self, elements, fitness_func):
        super().__init__(elements, fitness_func)

        self.ADD_MUTATION_COUNT = 4
        self.SUB_MUTATION_COUNT = 2
        self.CH_MUTATION_COUNT = 2

        creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
        creator.create("Individual", OrderedSet, fitness=creator.FitnessMin)
        toolbox = base.Toolbox()
        toolbox.register("attr_item", pick_index_biased, self.elements_map)

        toolbox.register("individual", tools.initRepeat,
                         creator.Individual, toolbox.attr_item, self.sequence_length)
        toolbox.register("population", tools.initRepeat,
                         list, toolbox.individual)

        # toolbox.register("mate", tools.cxUniform, indpb=0.5)
        # toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1)
        toolbox.register("mate", self.mate)
        toolbox.register("mutate", self.mutate)
        toolbox.register("select", tools.selNSGA2)
        toolbox.register("evaluate", self.evaluate)

        self.toolbox = toolbox
        self.creator = creator

    def get_best_individual(self):
        pop = self.evolve_population()
        fitnesses = map(self.toolbox.evaluate, pop)

        best_fit = 10 ** 10
        best_ind = None
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit
            if fit[0] < best_fit:
                best_fit = fit[0]
                best_ind = ind

        print('best fitness: {}'.format(best_fit))
        return [self.elements[index] for index in best_ind]

    def mate(self, individual1, individual2, indpb):
        length = min(len(individual1), len(individual2))
        ind1 = list(individual1)
        ind2 = list(individual2)
        for index in range(length):
            if random.random() < indpb:
                ind1[index], ind2[index] \
                    = ind2[index], ind1[index]

        return self.creator.Individual(ind1), self.creator.Individual(ind2)

    def mutate(self, individual):

        def add_mutation():
            old_len = len(individual)
            while len(individual) < old_len + self.ADD_MUTATION_COUNT \
                    and len(individual) < len(self.elements):
                new_gene = pick_index_biased(self.elements_map)
                individual.add(new_gene)
            return individual

        def rm_mutation():
            old_len = len(individual)
            while len(individual) > old_len - self.SUB_MUTATION_COUNT \
                    and len(individual) > 1:
                rm_gene = random.sample(individual, 1)[0]
                individual.discard(rm_gene)
                return individual

        def ch_mutation():
            for i in range(self.CH_MUTATION_COUNT):
                individual_list = list(individual)
                ch_index = random.sample(range(len(individual_list)), 1)[0]
                ch_gene = pick_index_biased(self.elements_map)  # random.sample(range(len(self.elements)), 1)[0]
                individual_list[ch_index] = ch_gene
            return self.creator.Individual(individual_list)

        mutations = [add_mutation, rm_mutation, ch_mutation]
        mutation = random.sample(mutations, 1)[0]

        print(str(mutation))
        return mutation()

    def evaluate(self, individual):
        sequence = []
        for index in individual:
            sequence.append(self.elements[index])

        # a list of lists !?
        fit = self.fit([sequence])[0][0]
        # TODO: check is_applicable | self.fit([sequence])[0][1][0]
        return (float(fit), len(individual))

    def evolve_population(self, n=10, CXPB=0.5, MUTPB=0.2, NGEN=5):
        toolbox = self.toolbox

        pop = toolbox.population(n)
        print(pop)

        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        for g in range(NGEN):
            average_fitness = sum(
                map(lambda x: self.toolbox.evaluate(x)[0], pop)) / len(pop)
            if (str(g)[-1] == '0'):
                print('{}st generation: {}'.format(g + 1, average_fitness))
            elif (str(g)[-1] == '1'):
                print('{}nd generation: {}'.format(g + 1, average_fitness))
            elif (str(g)[-1] == '2'):
                print('{}rd generation: {}'.format(g + 1, average_fitness))
            else:
                print('{}th generation: {}'.format(g + 1, average_fitness))

            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2, 0.5)  # TODO: scale INDPB
                    del child1.fitness.values
                    del child2.fitness.values

            new_offspring = list()
            for mutant in offspring:
                if random.random() < MUTPB:
                    mutant = toolbox.mutate(mutant)
                    del mutant.fitness.values
                new_offspring.append(mutant)

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            pop[:] = offspring
            print(pop)

        return pop
