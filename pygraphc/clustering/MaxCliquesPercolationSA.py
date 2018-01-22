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
    def __init__(self, graph, edges_weight, nodes_id, tmin, tmax, alpha, energy_type, iteration_threshold,
                 brute_force, preprocessed_logs, log_length):
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
        self.brute_force = brute_force
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length

    def __get_maxcliques_percolation_weighted_sa(self, percolation_only=False):
        """The main method to run maximal clique percolation using simulated annealing.

        Parameters
        ----------
        percolation_only    : bool
            Flag for percolation. False means simulated annealing will run for two parameters:
            percolation (k) and intensity (I).

        Returns
        -------
        best_parameter      : dict
            The parameters that provide the best energy.
        best_cluster        : dict
            The best cluster generated using the best parameter.
        best_energy         : float
            The best energy based on specific type, i.e., Silhouette index or Dunn index.
        """
        best_parameter, best_cluster = {}, {}
        processed_parameter = []
        current_energy, best_energy = 0., 0.

        # get random parameters from the given range
        if not percolation_only:
            parameters, all_combinations = self.__set_parameters()
        else:
            parameters, all_combinations = self.__set_parameters(True)

        if parameters['k']:
            # create instance of simulated annealing utility
            sa = SimulatedAnnealing(self.Tmin, self.Tmax, self.alpha, parameters, self.max_iteration,
                                    self.preprocessed_logs, self.log_length)

            if not percolation_only:
                # get initial maximal clique percolation and its energy
                current_parameter = sa.get_parameter(processed_parameter, all_combinations, False, self.brute_force)
                processed_parameter.append((current_parameter['k'], current_parameter['I']))
                mcpw_sa_cluster = self.get_maxcliques_percolation_weighted(current_parameter['k'],
                                                                           current_parameter['I'])
            else:
                current_parameter = sa.get_parameter(processed_parameter, all_combinations, True, self.brute_force)
                processed_parameter.append(current_parameter['k'])
                mcpw_sa_cluster = self.get_maxcliques_percolation(current_parameter['k'])

            if mcpw_sa_cluster:
                current_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1
                best_energy = current_energy
                best_parameter = current_parameter
                best_cluster = mcpw_sa_cluster

                # print current parameter
                if current_parameter['k'] and current_parameter['I']:
                    print current_parameter['k'], ',', current_parameter['I'], ',', current_energy * -1

                # cooling the temperature
                tnew = sa.get_temperature(self.Tmax)

                # main loop of simulated annealing
                count_iteration = 0
                while tnew > self.Tmin and count_iteration <= self.max_iteration:
                    # reset current clique percolation before finding the new one
                    self.clique_percolation.clear()

                    # set perameter, find cluster, and get energy
                    tcurrent = tnew
                    if not percolation_only:
                        new_parameter = sa.get_parameter(processed_parameter, all_combinations, False, self.brute_force)
                        processed_parameter.append((new_parameter['k'], new_parameter['I']))
                        mcpw_sa_cluster = \
                            self.get_maxcliques_percolation_weighted(new_parameter['k'], new_parameter['I'])
                    else:
                        new_parameter = sa.get_parameter(processed_parameter, all_combinations, True, self.brute_force)
                        processed_parameter.append(new_parameter['k'])
                        mcpw_sa_cluster = self.get_maxcliques_percolation(new_parameter['k'])

                    if mcpw_sa_cluster:
                        new_energy = sa.get_energy(self.graph, mcpw_sa_cluster, self.energy_type) * -1
                    else:
                        new_energy = 0.

                    # print new parameter
                    if current_parameter['k'] and current_parameter['I']:
                        print new_parameter['k'], ',', new_parameter['I'], ',', new_energy * -1

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

        else:
            # no cluster found using both k and I
            best_parameter['k'] = -1
            best_parameter['I'] = -1
            best_energy = -1

            # a connected component becomes a cluster
            best_cluster = self._get_clusters()

            # if only one connected component found, then a node become a cluster
            if len(best_cluster) == 1:
                cluster_id = 0
                best_cluster = {}
                for node in self.graph.nodes_iter(data=True):
                    best_cluster[cluster_id] = [node[0]]
                    cluster_id += 1

        print 'best parameter and energy', best_parameter, best_energy
        return best_parameter, best_cluster, best_energy

    def __set_parameters(self, percolation_only=False):
        """Set initial parameter before running simulated annealing.

        Parameters
        ----------
        percolation_only    : bool
            Flag for percolation. False means simulated annealing will run for two parameters:
            percolation (k) and intensity (I).

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
        if not percolation_only:
            intensity = linspace(0.1, 0.9, 9)
            new_intensity = [round(intens, 1) for intens in intensity]

            parameters = {
                'k': k,
                'I': new_intensity
            }

            # max iteration is total number of all combinations between parameter k and I
            all_combinations = list(product(parameters['k'], parameters['I']))

        else:
            parameters = {'k': k}
            all_combinations = parameters['k']

        # all_combinations is reduced by 2:
        # 1 for initial process that does not include loop and 1 for zero-based index
        self.max_iteration = ceil(self.iteration_threshold * (len(all_combinations) - 2))
        return parameters, all_combinations

    def get_maxcliques_sa(self):
        """Main method to run maximal clique percolation and find its optimal parameter by simulated annealing.

        If there are no clusters found using parameter percolation (k) and intensity (I),
        we run the method only using k.

        Returns
        -------
        best_parameter      : dict
            The parameters that provide the best energy.
        best_cluster        : dict
            The best cluster generated using the best parameter.
        best_energy         : float
            The best energy based on specific type, i.e., Silhouette index or Dunn index.
        """
        best_parameter, best_cluster, best_energy = self.__get_maxcliques_percolation_weighted_sa()

        # no cluster found using I, use only k
        if not best_cluster:
            best_parameter, best_cluster, best_energy = self.__get_maxcliques_percolation_weighted_sa(True)
            best_parameter['I'] = 0.

        return best_parameter, best_cluster, best_energy
