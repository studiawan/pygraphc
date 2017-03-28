from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.optimization.SimulatedAnnealing import SimulatedAnnealing
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation
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
        # run initialization of max_clique
        self.init_maxclique_percolation()
        parameters = self.__set_parameters()

        sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.energy_type, self.max_iteration)
        current_parameter = sa.get_parameter({})

        # get maximal clique percolation
        self.init_maxclique_percolation()
        mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(current_parameter['k'], current_parameter['I'])
        current_energy = InternalEvaluation.get_silhoutte_index(self.graph, mcpw_sa_cluster)

        tcurrent = self.Tmax
        tnew = self.alpha * tcurrent
        count_iteration = 0
        best_parameter = {}
        while tnew > self.Tmin or count_iteration <= self.max_iteration:
            # set perameter, find cluster, get energy
            new_parameter = sa.get_parameter(current_parameter)
            mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(new_parameter['k'], new_parameter['I'])
            new_energy = InternalEvaluation.get_silhoutte_index(self.graph, mcpw_sa_cluster)

            # get delta energy and check
            delta_energy = new_energy - current_energy
            if new_energy <= current_energy:
                best_parameter = new_parameter
            elif exp(-delta_energy / tnew) > uniform(0, 1):
                best_parameter = new_parameter

            # cooling the temperature
            tnew = self.alpha * tnew
            count_iteration += 1

        return best_parameter

    def __set_parameters(self):
        # get maximal node for all maximal cliques to generate k
        max_node = 0
        for max_clique in self.cliques:
            current_len = len(max_clique)
            if max_node < current_len:
                max_node = current_len

        parameters = {
            'k': list(xrange(2, max_node)),
            'I': linspace(0.1, 0.9, 9)
        }

        self.max_iteration = len(list(product(parameters['k'], parameters['I'])))
        return parameters
