from numpy import average


class InternalEvaluation(object):
    """This a class for internal evaluation: validating cluster model without known ground truth.
    """
    @staticmethod
    def __get_avg_distance(graph, node, neighbors):
        """Get average distance from a node to its neighbor.

        The neighbors can be located in intra-cluster or inter-cluster. The distance means
        edge weight in the graph case.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        node        : int
            Node identifier in incremental integer.
        neighbors   : list
            List of neighbors' node identifier.

        Returns
        -------
        avg_distance    : float
            The average distance of node to its analyzed neighbors.
        """
        neigbors_weight = graph[node]
        distance = []
        for node_id, weight in neigbors_weight.iteritems():
            if node_id in neighbors:
                distance.append(weight['weight'])

        avg_distance = average(distance)
        return avg_distance

    @staticmethod
    def __get_node_silhoutte(graph, clusters):
        """Get node silhoutte.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        node_silhouttes : dict[int, float]
            A dictionary containing silhoutte per node. Key: node identifier, value: silhoutte.
        """
        # please note this method has not supported for cluster with only one node (singleton)
        cid = set(clusters.keys())
        intracluster_avg, intercluster_avg, node_silhouttes = {}, {}, {}

        for cluster_id, cluster in clusters.iteritems():
            # get average of intra-cluster distance
            for node in cluster:
                distance = InternalEvaluation.__get_avg_distance(graph, node, cluster)
                intracluster_avg[node] = distance

            # all cluster - current cluster, get all nodes in inter cluster
            neighbor_cluster = cid - {cluster_id}
            intercluster_nodes = []
            for neighbor in neighbor_cluster:
                intercluster_nodes += clusters[neighbor]

            # get average of inter-cluster distance
            for node in cluster:
                distance = InternalEvaluation.__get_avg_distance(graph, node, intercluster_nodes)
                intercluster_avg[node] = distance

            # get vertex silhoutte
            node_silhouttes[node] = (intercluster_avg[node] - intracluster_avg[node]) / max(intercluster_avg[node],
                                                                                            intracluster_avg[node])
        return node_silhouttes

    @staticmethod
    def __get_cluster_silhoutte(graph, clusters):
        """Get cluster silhoutte.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        cluster_silhouttes  : dict[int, float]
            A dictionary containing silhoutte per cluster. Key: cluster identifier, value: silhoutte.
        """
        node_silhouttes = InternalEvaluation.__get_node_silhoutte(graph, clusters)
        cluster_silhouttes = {}
        for cluster_id, cluster in clusters.iteritems():
            silhoutte = []
            for node in cluster:
                silhoutte.append(node_silhouttes[node])
            cluster_silhouttes[cluster_id] = average(silhoutte)

        return cluster_silhouttes

    @staticmethod
    def get_silhoutte_index(graph, clusters):
        """Get silhoutte index for a graph.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        silhoutte_index : float
            The silhoutte index for a graph.
        """
        cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(graph, clusters)
        silhoutte_index = average(cluster_silhouttes.values())

        return silhoutte_index
