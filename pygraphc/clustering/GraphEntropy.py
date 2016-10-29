from math import log


class GraphEntropy(object):
    def __init__(self, graph):
        self.graph = graph

    def get_node_entropy(self, cluster_candidate, node):
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

    def get_entropies(self, cluster_candidate):
        entropies = {}
        for node in self.graph.nodes():
            entropies[node] = self.get_node_entropy(cluster_candidate, node)
        return entropies

    def get_graph_entropy(self):
        nodes = self.graph.nodes()
        # clusters = []
        cluster_candidate = []
        entropies = {}
        for node in nodes:
            initial_node = node
            cluster_candidate = self.graph.neighbors(initial_node)
            cluster_candidate.append(initial_node)
            entropies = self.get_entropies(cluster_candidate)

            # removing neighbors to minimize entropy
            for n in cluster_candidate:
                if n == node:   # don't remove our seed, obviously
                    continue
                else:
                    new_cluster = list(cluster_candidate)
                    new_cluster.remove(n)
                    new_entropies = self.get_entropies(new_cluster)

                    if sum(new_entropies.itervalues()) < sum(entropies[v] for v in cluster_candidate):
                        cluster_candidate = new_cluster
                        entropies.update(new_entropies)

        # boundary candidates
        c = reduce(lambda a, b: a | b, (set(self.graph.neighbors(v)) for v in cluster_candidate)) - cluster_candidate
        while c:
            n = c.pop()
            new_cluster = list(cluster_candidate)
            new_cluster.append(n)
            new_entropies = self.get_entropies(new_cluster)

            if sum(new_entropies.itervalues()) < sum(entropies[v] for v in cluster_candidate):
                cluster_candidate = new_cluster
                entropies.update(new_entropies)
                c &= set(self.graph.neighbors(n)) - cluster_candidate

        nodes -= cluster_candidate

        if len(cluster_candidate) > 1:
            print ' '.join(c for c in cluster_candidate)
