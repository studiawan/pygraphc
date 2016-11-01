from math import log


class GraphEntropy(object):
    def __init__(self, graph):
        self.graph = graph
        self.clusters = []

    def get_graph_entropy(self):
        nodes = set(self.graph.nodes())

        while nodes:
            seed_node = nodes.pop()
            cluster_candidate = set(self.graph.neighbors(seed_node))
            cluster_candidate.add(seed_node)
            entropies = self._get_entropies(cluster_candidate, self.graph.nodes())

            # removing neighbors to minimize entropy
            for node in list(cluster_candidate):
                if node == seed_node:   # don't remove the seed node
                    continue

                new_cluster = cluster_candidate.copy()
                new_cluster.remove(node)
                new_entropies = self._get_entropies(new_cluster, self.graph.neighbors(node))

                if sum(new_entropies.itervalues()) < sum(entropies[v] for v in self.graph.neighbors(node)):
                    cluster_candidate = new_cluster
                    entropies.update(new_entropies)

            # boundary candidates, a intersection with b
            c = reduce(lambda a, b: a | b, (set(self.graph.neighbors(v)) for v in cluster_candidate)) - \
                cluster_candidate

            while c:
                node = c.pop()
                new_cluster = cluster_candidate.copy()
                new_cluster.add(node)
                new_entropies = self._get_entropies(new_cluster, self.graph.neighbors(node))

                if sum(new_entropies.itervalues()) < sum(entropies[v] for v in self.graph.neighbors(node)):
                    cluster_candidate = new_cluster
                    entropies.update(new_entropies)
                    c &= set(self.graph.neighbors(node)) - cluster_candidate

            nodes -= cluster_candidate

            if len(cluster_candidate) > 0:
                print '-'.join(str(c) for c in cluster_candidate)

    def _get_entropies(self, cluster_candidate, neighbors):
        entropies = {}
        for node in neighbors:
            entropies[node] = self._get_node_entropy(cluster_candidate, node)

        return entropies

    def _get_node_entropy(self, cluster_candidate, node):
        # get node degree with weight
        degree = self.graph.degree(weight='weight')[node]
        if degree == 0:
            return 0

        # get inner link/edge probability
        neighbors_weight = self.graph[node]
        neighbors_weight_sum = 0
        for node_id, weight in neighbors_weight.iteritems():
            if node_id in cluster_candidate:
                neighbors_weight_sum += weight[0]['weight']
        inner_probability = neighbors_weight_sum / degree

        # get entropy
        entropy = 0 if inner_probability <= 0.0 or inner_probability >= 1.0 else \
            -inner_probability * log(inner_probability, 2) - (1 - inner_probability) * log(1 - inner_probability, 2)

        # print 'entropy', node, entropy
        return entropy
