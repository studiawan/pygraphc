from MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.optimization.SimulatedAnnealing import SimulatedAnnealing
from numpy import linspace


class MaxCliquesPercolationSA(MaxCliquesPercolationWeighted):
    def __init__(self, graph, edges_weight, nodes_id, k, threshold, tmin, tmax, alpha, energy_type, max_iteration):
        super(MaxCliquesPercolationSA, self).__init__(graph, edges_weight, nodes_id, k, threshold)
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.energy_type = energy_type
        self.max_iteration = max_iteration

    def get_maxcliques_percolation_sa(self):
        # run max_clique
        max_cliques = self._find_maxcliques()

        # get maximal node for all maximal cliques to generate k
        max_node = 0
        for max_clique in max_cliques:
            current_len = len(max_clique)
            if max_node < current_len:
                max_node = current_len

        parameters = {
            'k': list(xrange(2, max_node)),
            'I': linspace(0.1, 0.9, 9)
        }

        sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.energy_type, self.max_iteration)
        initial_parameter = sa.get_parameter()

        # get maximal clique percolation
