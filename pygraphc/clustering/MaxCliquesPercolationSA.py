from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.optimization.SimulatedAnnealing import SimulatedAnnealing
from numpy import linspace
from math import exp
from random import uniform
from itertools import product


class MaxCliquesPercolationSA(MaxCliquesPercolationWeighted):
    def __init__(self, graph, edges_weight, nodes_id, tmin, tmax, alpha, energy_type):
        super(MaxCliquesPercolationSA, self).__init__(graph, edges_weight, nodes_id)
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.energy_type = energy_type
        self.max_iteration = 0

    def get_maxcliques_percolation_sa(self):
        # get random parameters from the given range
        parameters = self.__set_parameters()

        # create simulated annealing utility instance
        sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.max_iteration)
        current_parameter = sa.get_parameter({})

        # get initial maximal clique percolation and its energy
        self.init_maxclique_percolation()
        mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(current_parameter['k'], current_parameter['I'])
        current_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type)

        # cooling the temperature
        tnew = sa.get_temperature(self.Tmax)

        # main loop of simulated annealing
        count_iteration = 0
        best_parameter = {}
        while tnew > self.Tmin or count_iteration <= self.max_iteration:
            # set perameter, find cluster, get energy
            tcurrent = tnew
            new_parameter = sa.get_parameter(current_parameter)
            mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(new_parameter['k'], new_parameter['I'])
            new_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type)

            # get delta energy and check
            delta_energy = new_energy - current_energy
            if new_energy <= current_energy:
                best_parameter = new_parameter
            elif exp(-delta_energy / tcurrent) > uniform(0, 1):
                best_parameter = new_parameter
            current_energy = new_energy

            # cooling the temperature
            tnew = sa.get_temperature(tcurrent)
            count_iteration += 1

        return best_parameter

    def __set_parameters(self):
        # get maximal node for all maximal cliques to generate k
        max_node = 0
        for max_clique in self.cliques:
            current_len = len(max_clique)
            if max_node < current_len:
                max_node = current_len

        # set parameter k (number of percolation) and I (intensity threshold)
        parameters = {
            'k': list(xrange(2, max_node)),
            'I': linspace(0.1, 0.9, 9)
        }

        # max iteration is total number of all combinations between parameter k and I
        self.max_iteration = len(list(product(parameters['k'], parameters['I'])))
        return parameters
