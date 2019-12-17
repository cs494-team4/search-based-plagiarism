import random
import pickle
import os

import numpy
import matplotlib.pyplot as plt


from deap import base
from deap import creator
from deap import tools

from metaheuristics.FitnessOptimizer import FitnessOptimizer
from utils import OrderedSet
from utils.nsga import sortNondominated

NUM_POP = 25
CXPB = 0.5
MUTPB = 0.7
NGEN = 100
INITIAL_SEQUENCE_LEN = 15


class FitnessCalculationException(Exception):
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class Population():
    def __init__(self, population, generation):
        pop_list = []
        for ind in population:
            pop_list.append(list(ind))

        self.population = pop_list
        self.gen_number = generation


def pick_index_biased(elements_map):
    r_types = elements_map.keys()

    type_index = random.randrange(len(r_types))
    r_type = list(r_types)[type_index]
    target_index = random.randrange(len(elements_map[r_type]))

    return elements_map[r_type][target_index][1]


class GAOptimizer(FitnessOptimizer):
    def __init__(self, elements, fitness_func):
        super().__init__(elements, fitness_func)

        self.ADD_MUTATION_COUNT = 6
        self.SUB_MUTATION_COUNT = 8
        self.CH_MUTATION_COUNT = 4

        self.sequence_length = INITIAL_SEQUENCE_LEN
        self.archive = []

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
        try:
            pop = self.evolve_population()
            fitnesses = map(self.toolbox.evaluate, pop)
        except FitnessCalculationException:
            with open('saved_population.pkl', 'wb') as f:
                pickle.dump(self.population, f)
                print(
                    "Server Error: But don't worry. Current population was saved as saved_population.pkl")

                exit(0)

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
        ind1 = list(individual1)
        ind2 = list(individual2)
        swapped = False

        if len(ind2) < len(ind1):
            swapped = True
            ind1, ind2 = ind2, ind1     # ind1 has smaller or equal length than ind2
        len_short = len(ind1)
        len_long = len(ind2)

        for index in range(len_short):
            ind1[index], ind2[index] \
                = ind2[index], ind1[index]
        for remain_i in range(len_long - len_short):
            ind1.append(ind2[len_short + remain_i])
            ind2[len_short + remain_i] = -1
        ind2 = [i for i in ind2 if i >= 0]

        if swapped:
            ind2, ind1 = ind1, ind2

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
                # random.sample(range(len(self.elements)), 1)[0]
                ch_gene = pick_index_biased(self.elements_map)
                individual_list[ch_index] = ch_gene
            return self.creator.Individual(individual_list)

        mutations = [add_mutation, rm_mutation, ch_mutation]
        mutation = random.sample(mutations, 1)[0]

        # print(str(mutation))
        return mutation()

    def evaluate(self, individual):
        sequence = []
        for index in individual:
            sequence.append(self.elements[index])

        # a list of lists !?
        try:
            fit = self.fit([sequence])[0][0]
        except (ValueError, IOError) as e:
            raise FitnessCalculationException(
                e, "Error while getting fitness value from server")
        # TODO: check is_applicable | self.fit([sequence])[0][1][0]
        return float(fit), len(individual)

    def evolve_population(self, n=NUM_POP, CXPB=CXPB, MUTPB=MUTPB, NGEN=NGEN):
        toolbox = self.toolbox

        start_gen = 0

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean, axis=0)
        stats.register("std", numpy.std, axis=0)
        stats.register("min", numpy.min, axis=0)
        stats.register("max", numpy.max, axis=0)

        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "std", "min", "avg", "max"

        pop = toolbox.population(n)

        if os.path.isfile('saved_population.pkl'):
            with open('saved_population.pkl', 'rb') as f:
                p = pickle.load(f)
                pop = list(
                    map(lambda x: self.creator.Individual(set(x)), p.population))
                start_gen = p.gen_number
                print("start from {}th generation".format(start_gen))

        self.population = Population(pop, start_gen)
        # print(pop)

        fitnesses = map(toolbox.evaluate, pop)

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        # Compile statistics about the population
        record = stats.compile(pop)
        logbook.record(gen=0, evals=len(pop), **record)
        # print("logbook stream of first: ", logbook.stream)

        def show_plot(g):
            fronts = sortNondominated(self.archive, k=len(self.archive))
            fronts_to_print = []

            for n in range(min(5, len(fronts))):
                dominating_group = sorted(
                    [self.archive[i] for i in fronts[n]], key=lambda individual: individual.fitness.values[0])

                print("{}: ".format(n), list(
                    map(lambda i: list(map(lambda e: self.elements[e], i)), dominating_group)))
                print('\n')
                print("fitness values(scores): ", list(
                    map(lambda i: i.fitness.values[0], dominating_group)))
                print("fitness values(lengths): ", list(
                    map(lambda i: i.fitness.values[1], dominating_group)))
                print("{}: ".format(n), dominating_group)
                for ind in dominating_group:
                    print(self.count_indivudial_refatorings(ind))

                fronts_to_print.append(numpy.array(
                    [ind.fitness.values for ind in dominating_group]))

            fig = plt.figure(figsize=(6, 6))

            colors = ['p', 'b', 'g', 'y', 'r']

            for n in range(min(5, len(fronts_to_print))):
                plt.plot(fronts_to_print[n][:, 1], fronts_to_print[n][:, 0],
                         colors[n], marker='o', markersize=6, linestyle='-')

            plt.title('Pareto Fronts of the {} Generation'.format(g))
            plt.xlabel('number of refactorings')
            plt.ylabel('similarity score(%)')
            plt.savefig('figs/{}_gen{}.png'.format(id(self.archive), g))

        for g in range(start_gen, NGEN):

            # Select the next generation individuals
            offspring = toolbox.select(pop, len(pop))
            # Clone the selected individuals
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2, 1)
                    del child1.fitness.values
                    del child2.fitness.values

            new_offspring = list()
            for mutant in offspring:
                if random.random() < MUTPB:
                    mutant = toolbox.mutate(mutant)
                    del mutant.fitness.values
                new_offspring.append(mutant)

            # Evaluate the individuals with an invalid fitness
            fitnesses = map(toolbox.evaluate, offspring)

            for ind, fit in zip(offspring, fitnesses):
                ind.fitness.values = fit

            # The population is entirely replaced by the offspring
            pop[:] = offspring
            self.population = Population(pop, g+1)

            fronts = sortNondominated(pop, k=len(pop))
            best_front = [pop[i] for i in fronts[0]]
            self.archive.extend(best_front)
            if g % 10 == 0:
                show_plot('{}th'.format(g+1))
            # print(pop)

            record = stats.compile(pop)
            logbook.record(gen=g+1, evals=len(offspring), **record)
            # print("logbook stream: ", logbook.stream)
            # print("lenpop: ", len(pop))
            average_fitness = sum(
                map(lambda x: self.toolbox.evaluate(x)[0], pop)) / len(pop)
            if str(g)[-1] == '0':
                print('Result of {}st generation: {}'.format(
                    g + 1, average_fitness))
                if g < NGEN-1:
                    print('Start of {}nd generation'.format(g+2))
                else:
                    print('End of Evolution')
            elif str(g)[-1] == '1':
                print('Result of {}nd generation: {}'.format(
                    g + 1, average_fitness))
                if g < NGEN-1:
                    print('Start of {}rd generation'.format(g+2))
                else:
                    print('End of Evolution')
            elif str(g)[-1] == '2':
                print('Result of {}rd generation: {}'.format(
                    g + 1, average_fitness))
                if g < NGEN-1:
                    print('Start of {}th generation'.format(g+2))
                else:
                    print('End of Evolution')
            else:
                print('Result of {}th generation: {}'.format(
                    g + 1, average_fitness))
                if g < NGEN-1:
                    print('Start of {}th generation'.format(g+2))
                else:
                    print('End of Evolution')

        # plot pareto front
        self.archive.extend(pop)

        show_plot('last')

        return pop

    def count_indivudial_refatorings(self, individual):
        counting_dict = dict()
        for key in self.elements_map.keys():
            counting_dict[key] = 0

        print()
        for ref in individual:
            _type, _ = self.elements[ref]
            counting_dict[_type] += 1

        return counting_dict
