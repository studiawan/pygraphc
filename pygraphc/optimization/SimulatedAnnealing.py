from random import choice
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation


class SimulatedAnnealing(object):
    def __init__(self, tmin, tmax, alpha, parameters, max_iteration):
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

    def get_parameter(self, previous_parameter):
        """Get random parameter based on given range.

        Returns
        -------
        random_parameter    : dict
            Dictionary of random parameters.
        """
        random_parameter = {}
        while True:
            for param, value in self.parameters.iteritems():
                random_parameter[param] = choice(value)

            # make sure generated parameter is not the same as previous parameter
            if random_parameter != previous_parameter:
                break

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

    @staticmethod
    def get_energy(graph, clusters, energy_type):
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
        energy = 0.
        if energy_type == 'silhoutte':
            energy = InternalEvaluation.get_silhoutte_index(graph, clusters)

        return energy
