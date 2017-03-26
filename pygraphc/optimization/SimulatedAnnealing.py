from random import choice
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation


class SimulatedAnnealing(object):
    def __init__(self, tmin, tmax, alpha, parameters, energy_type, max_iteration):
        """The constructor of Simulated Annealing method.

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
        energy_type     : str
            Objective function of simulated annealing. We use internal evaluation for graph clustering.
        max_iteration   : int
            Maximum iteration for simulated annealing.
        """
        self.Tmin = tmin
        self.Tmax = tmax
        self.alpha = alpha
        self.parameters = parameters
        self.energy_type = energy_type
        self.max_iteration = max_iteration

    def get_parameter(self):
        """Get random parameter based on given range.

        Returns
        -------
        random_parameter    : dict[str, float]
            Dictionary of random parameters.
        """
        random_parameter = {}
        for param, value in self.parameters.iteritems():
            random_parameter[param] = choice(value)

        return random_parameter

    def get_temperature(self, current_temperature):
        new_temperature = self.alpha * current_temperature
        return new_temperature

    def get_energy(self, graph, clusters):
        energy = 0.
        if self.energy_type == 'silhoutte':
            energy = InternalEvaluation.get_silhoutte_index(graph, clusters)

        return energy
