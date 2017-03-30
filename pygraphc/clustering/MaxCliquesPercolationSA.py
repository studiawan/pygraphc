from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.optimization.SimulatedAnnealing import SimulatedAnnealing
from numpy import linspace
from math import exp
from random import uniform
from itertools import product


class MaxCliquesPercolationSA(MaxCliquesPercolationWeighted):
    """Get clustering based on maximal clique percolation and the parameters are optimized
       using simulated annealing.
    """
    def __init__(self, graph, edges_weight, nodes_id, tmin, tmax, alpha, energy_type):
        """The constructor of class MaxCliquesPercolationSA.

        Parameters
        ----------
        graph           : graph
            Graph to be clustered.
        edges_weight    : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id        : list
            List of all node identifier.
        tmin            : float
            Minimum temperature.
        tmax            : float
            Maximum temperature.
        alpha           : float
            Cooling factor or temperature multiplier.
        energy_type     : str
            Type of energy or objective function such as Silhoutte index, Dunn index, etc.
        """
        super(MaxCliquesPercolationSA, self).__init__(graph, edges_weight, nodes_id)
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.energy_type = energy_type
        self.max_iteration = 0

    def get_maxcliques_percolation_weighted_sa(self):
        """The main method to run maximal clique percolation using simulated annealing.

        Returns
        -------
        best_parameter  : dict
            The parameters that provide the best energy.
        """
        # get random parameters from the given range
        parameters = self.__set_parameters()
        best_parameter, best_cluster = {'k': [], 'I': []}, {}
        if parameters['k']:
            # create simulated annealing utility instance
            sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.max_iteration)
            current_parameter = sa.get_parameter({})

            # get initial maximal clique percolation and its energy
            self.init_maxclique_percolation()
            mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(current_parameter['k'], current_parameter['I'])
            current_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1

            # cooling the temperature
            tnew = sa.get_temperature(self.Tmax)

            # main loop of simulated annealing
            count_iteration = 0
            while tnew > self.Tmin or count_iteration <= self.max_iteration:
                # set perameter, find cluster, get energy
                tcurrent = tnew
                new_parameter = sa.get_parameter(current_parameter)
                mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(new_parameter['k'], new_parameter['I'])
                new_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1

                # get delta energy and check
                delta_energy = new_energy - current_energy
                if new_energy <= current_energy:
                    best_parameter = new_parameter
                    best_cluster = mcpw_sa_cluster
                elif exp(-delta_energy / tcurrent) > uniform(0, 1):
                    best_parameter = new_parameter
                    best_cluster = mcpw_sa_cluster
                current_energy = new_energy

                # cooling the temperature
                tnew = sa.get_temperature(tcurrent)
                count_iteration += 1

        return best_parameter, best_cluster

    def __set_parameters(self):
        """Set initial parameter before running simulated annealing.

        Returns
        -------
        parameters  : dict
            Initial parameter to run. Key: variable name, value: list of possible values.
        """
        # get maximal node for all maximal cliques to generate k
        max_node = 0
        for max_clique in self.cliques:
            current_len = len(max_clique)
            if max_node < current_len:
                max_node = current_len

        # set parameter k (number of percolation) and I (intensity threshold)
        k = list(xrange(2, max_node)) if max_node > 0 else []
        parameters = {
            'k': k,
            'I': linspace(0.1, 0.9, 9)
        }

        # max iteration is total number of all combinations between parameter k and I
        self.max_iteration = len(list(product(parameters['k'], parameters['I'])))
        return parameters
