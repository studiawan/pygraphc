from numpy import average


class InternalEvaluation(object):
    @staticmethod
    def get_avg_distance(graph, node, neighbors):
        # neighbors can be located in intra-cluster or inter-cluster
        neigbors_weight = graph[node]
        distance = []
        for node_id, weight in neigbors_weight.iteritems():
            if node_id in neighbors:
                distance.append(weight['weight'])

        avg_distance = average(distance)
        return avg_distance

    @staticmethod
    def get_node_silhoutte(graph, clusters):
        # please check for cluster with only one node
        cid = set(clusters.keys())
        intracluster_avg, intercluster_avg, node_silhouttes = {}, {}, {}

        for cluster_id, cluster in clusters.iteritems():
            # get average of intra-cluster distance
            for node in cluster:
                distance = InternalEvaluation.get_avg_distance(graph, node, cluster)
                intracluster_avg[node] = distance

            # all cluster - current cluster, get all nodes in inter cluster
            neighbor_cluster = cid - {cluster_id}
            intercluster_nodes = []
            for neighbor in neighbor_cluster:
                intercluster_nodes += clusters[neighbor]

            # get average of inter-cluster distance
            for node in cluster:
                distance = InternalEvaluation.get_avg_distance(graph, node, intercluster_nodes)
                intercluster_avg[node] = distance

            # get vertex silhoutte
            node_silhouttes[node] = (intercluster_avg[node] - intracluster_avg[node]) / max(intercluster_avg[node],
                                                                                            intracluster_avg[node])
        return node_silhouttes

    @staticmethod
    def get_cluster_silhoutte(graph, clusters):
        node_silhouttes = InternalEvaluation.get_node_silhoutte(graph, clusters)
        cluster_silhouttes = {}
        for cluster_id, cluster in clusters.iteritems():
            silhoutte = []
            for node in cluster:
                silhoutte.append(node_silhouttes[node])
            cluster_silhouttes[cluster_id] = average(silhoutte)

        return cluster_silhouttes

    @staticmethod
    def get_silhoutte_index(graph, clusters):
        cluster_silhouttes = InternalEvaluation.get_cluster_silhoutte(graph, clusters)
        silhoutte_index = average(cluster_silhouttes.values())

        return silhoutte_index
