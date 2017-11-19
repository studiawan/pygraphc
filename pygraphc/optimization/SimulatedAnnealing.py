from random import choice
from pygraphc.evaluation.EvaluationUtility import EvaluationUtility
from pygraphc.evaluation.CalinskiHarabaszIndex import CalinskiHarabaszIndex
from pygraphc.evaluation.DaviesBouldinIndex import DaviesBouldinIndex
from pygraphc.evaluation.XieBeniIndex import XieBeniIndex


class SimulatedAnnealing(object):
    def __init__(self, tmin, tmax, alpha, parameters, max_iteration, preprocessed_logs, log_length):
        """The utility class for Simulated Annealing method.

        Parameters
        ----------
        tmin            : float
            Minimum temperature.
        tmax            : float
            Maximum temperature.
        alpha           : float
            Cooling factor. Tnew = alpha * Tcurrent
        parameters      : dict
            Dictionary of parameters. Key: parameters, value: list.
        max_iteration   : int
            Maximum iteration for simulated annealing.
        """
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.parameters = parameters
        self.max_iteration = max_iteration
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length

    def get_parameter(self, previous_parameter, all_combinations, percolation_only=False, bruteforce=False):
        """Get random parameter based on given range.

        Parameters
        ----------
        previous_parameter  : list
            List of tuple containing all previous parameters, e.g., k and I: (k, I)
        all_combinations    : list
            List of all possible combinations of the parameter.
        percolation_only    : bool
            Flag for percolation. False means simulated annealing will run for two parameters:
            percolation (k) and intensity (I).
        bruteforce          : bool
            Flag for using brute force or not.

        Returns
        -------
        random_parameter    : dict
            Dictionary of random parameters.
        """
        random_parameter = {}
        if not bruteforce:
            while True:
                for param, value in self.parameters.iteritems():
                    random_parameter[param] = choice(value)
                if len(self.parameters['k']) == 1:
                    break
                # make sure generated parameter is not the same as previous parameter
                if not percolation_only:
                    if (random_parameter['k'], random_parameter['I']) not in previous_parameter:
                        break
                else:
                    if random_parameter['k'] not in previous_parameter:
                        break
        else:
            for param in all_combinations:
                if param not in previous_parameter:
                    if not percolation_only:
                        random_parameter['k'] = param[0]
                        random_parameter['I'] = param[1]
                    else:
                        random_parameter['k'] = param

        return random_parameter

    def get_temperature(self, current_temperature):
        """Get new parameter after cooling by alpha factor.

        Parameters
        ----------
        current_temperature : float
            Current temperature.

        Returns
        -------
        new_temperature     : float
            New temperature.
        """
        new_temperature = self.alpha * current_temperature
        return new_temperature

    def get_energy(self, graph, clusters, energy_type):
        """Get energy.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        energy_type : str
            Objective function of simulated annealing. We use internal evaluation for graph clustering.

        Returns
        -------
        energy  : float
            Current energy based on a specific internal or evaluation metric.
        """
        # convert clustering result from graph to text
        new_clusters = EvaluationUtility.convert_to_text(graph, clusters)

        energy = 0.
        if energy_type == 'calinski_harabasz':
            ch = CalinskiHarabaszIndex(new_clusters, self.preprocessed_logs, self.log_length)
            energy = ch.get_calinski_harabasz()
        elif energy_type == 'davies_bouldin':
            db = DaviesBouldinIndex(new_clusters, self.preprocessed_logs, self.log_length)
            energy = db.get_davies_bouldin()
        elif energy_type == 'xie_beni':
            xb = XieBeniIndex(new_clusters, self.preprocessed_logs, self.log_length)
            energy = xb.get_xie_beni()

        return energy
