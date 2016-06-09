
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
    def set_cluster_id(graph, clusters):
        cluster_id = 1
        for cluster in clusters:
            for node in cluster:
                graph.node[node]['cluster'] = cluster_id
            cluster_id += 1