from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.optimization.SimulatedAnnealing import SimulatedAnnealing
from numpy import linspace
from math import exp, ceil
from random import uniform
from itertools import product


class MaxCliquesPercolationSA(MaxCliquesPercolationWeighted):
    """Get clustering based on maximal clique percolation and the parameters are optimized
       using simulated annealing.
    """
    def __init__(self, graph, edges_weight, nodes_id, tmin, tmax, alpha, energy_type, iteration_threshold):
        """The constructor of class MaxCliquesPercolationSA.

        Parameters
        ----------
        graph               : graph
            Graph to be clustered.
        edges_weight        : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id            : list
            List of all node identifier.
        tmin                : float
            Minimum temperature.
        tmax                : float
            Maximum temperature.
        alpha               : float
            Cooling factor or temperature multiplier.
        energy_type         : str
            Type of energy or objective function such as Silhoutte index, Dunn index, etc.
        iteration_threshold : float
            Threshold for maximum iteration. For example the value 0.8 means that it only need to have
            80% of maximum iteration. We use maximum iteration when activating brute force mode.
        """
        super(MaxCliquesPercolationSA, self).__init__(graph, edges_weight, nodes_id)
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.energy_type = energy_type
        self.max_iteration = 0
        self.iteration_threshold = iteration_threshold

    def get_maxcliques_percolation_weighted_sa(self):
        """The main method to run maximal clique percolation using simulated annealing.

        Returns
        -------
        best_parameter  : dict
            The parameters that provide the best energy.
        """
        # get random parameters from the given range
        parameters, all_combinations = self.__set_parameters()
        best_parameter, best_cluster = {'k': [], 'I': []}, {}
        processed_parameter = []
        current_energy, best_energy = 0., 0.
        if parameters['k']:
            # create instance of simulated annealing utility
            sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.max_iteration)
            current_parameter = sa.get_parameter(processed_parameter, all_combinations, True)
            processed_parameter.append((current_parameter['k'], current_parameter['I']))

            # get initial maximal clique percolation and its energy
            mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(current_parameter['k'], current_parameter['I'])
            if mcpw_sa_cluster:
                current_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1
                best_energy = current_energy
                best_parameter = current_parameter
                best_cluster = mcpw_sa_cluster

            # cooling the temperature
            tnew = sa.get_temperature(self.Tmax)

            # main loop of simulated annealing
            count_iteration = 0
            while tnew > self.Tmin and count_iteration <= self.max_iteration:
                # reset clique percolation. this is the bug I am looking for a week. I forget to reset this variable.
                self.clique_percolation.clear()

                # set perameter, find cluster, get energy
                tcurrent = tnew
                new_parameter = sa.get_parameter(processed_parameter, all_combinations, True)
                processed_parameter.append((new_parameter['k'], new_parameter['I']))

                mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(new_parameter['k'], new_parameter['I'])
                if mcpw_sa_cluster:
                    new_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1
                else:
                    new_energy = 0.

                # get delta energy and check
                delta_energy = new_energy - current_energy
                if new_energy <= current_energy:
                    if new_energy <= best_energy:
                        best_energy = new_energy
                        best_parameter = new_parameter
                        best_cluster = mcpw_sa_cluster
                    else:
                        current_energy = new_energy
                elif exp(-delta_energy / tcurrent) > uniform(0, 1):
                    current_energy = new_energy

                # cooling the temperature
                tnew = sa.get_temperature(tcurrent)
                count_iteration += 1

        return best_parameter, best_cluster, best_energy

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
        intensity = linspace(0.1, 0.9, 9)
        new_intensity = []
        for intens in intensity:
            new_intensity.append(round(intens, 1))

        parameters = {
            'k': k,
            'I': new_intensity
        }

        # max iteration is total number of all combinations between parameter k and I
        all_combinations = list(product(parameters['k'], parameters['I']))

        # all_combinations is reduced by 2:
        # 1 for initial process that does not include loop and 1 for zero-based index
        self.max_iteration = ceil(self.iteration_threshold * (len(all_combinations) - 2))
        return parameters, all_combinations
