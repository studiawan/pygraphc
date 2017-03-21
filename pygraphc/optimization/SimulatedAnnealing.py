from random import choice
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation


class SimulatedAnnealing(object):
    def __init__(self, method, tmin, tmax, parameter, energy_type):
        """The constructor of Simulated Annealing method.

        Parameters
        ----------
        method      : str
            The method to run with simulated annealing.
        tmin        : float
            Minimum temperature.
        tmax        : float
            Maximum temperature.
        parameter   : dict
            Dictionary of parameter. Key: parameter, value: list.
        energy_type      : str
            Objective function of simulated annealing. We use internal evaluation for graph clustering.
        """
        self.method = method
        self.Tmin = tmin
        self.Tmax = tmax
        self.parameter = parameter
        self.energy_type = energy_type

    def __get_parameter(self):
        chosen_parameter = {}
        for param, value in self.parameter.iteritems():
            chosen_parameter[param] = choice(value)

        return chosen_parameter

    def __run_method(self):
        if self.method == 'max_clique':
            pass

    def __get_energy(self, graph, clusters):
        energy = 0.
        if self.energy_type == 'silhoutte':
            energy = InternalEvaluation.get_silhoutte_index(graph, clusters)

        return energy
