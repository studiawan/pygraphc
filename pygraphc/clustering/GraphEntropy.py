from math import log


class GraphEntropy(object):
    def __init__(self, graph):
        self.graph = graph

    def node_entropy(self, cluster_candidate, node):
        # get node degree with weight
        degree = self.graph.degree(weight='weight')[node]
        if degree == 0:
            return 0

        # get inner link/edge probability
        neighbors_weight = self.graph[node]
        neighbors_weight_sum = 0
        for node_id, weight in neighbors_weight.iteritems():
            if node_id in cluster_candidate:
                neighbors_weight_sum += weight['weight']
        inner_probability = neighbors_weight_sum / degree

        # get entropy
        entropy = 0 if inner_probability <= 0.0 or inner_probability >= 1.0 else \
            -inner_probability * log(inner_probability, 2) - (1 - inner_probability) * log(1 - inner_probability, 2)

        return entropy
