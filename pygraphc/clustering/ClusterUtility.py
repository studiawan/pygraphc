from itertools import combinations


class ClusterUtility(object):
    @staticmethod
    def get_geometric_mean(weights):
        multiplication = 1
        for weight in weights:
            multiplication = multiplication * weight

        gmean = 0.0
        multiplication = round(multiplication, 5)
        if multiplication > 0.0:
            k = float(len(weights))
            gmean = multiplication ** (1 / k)

        return round(gmean, 5)

    @staticmethod
    def get_weighted_cliques(graph, cliques, threshold):
        weighted_kcliques = []
        for clique in cliques:
            weights = []
            for u, v in combinations(clique, 2):
                reduced_precision = round(graph[u][v]['weight'], 5)
                weights.append(reduced_precision)
            gmean = ClusterUtility.get_geometric_mean(weights)

            if gmean > threshold:
                weighted_kcliques.append(frozenset(clique))

        return weighted_kcliques

    @staticmethod
    def set_cluster_id(graph, clusters):
        cluster_id = 0
        for cluster in clusters:
            for node in cluster:
                graph.node[node]['cluster'] = cluster_id
            cluster_id += 1