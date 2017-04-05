from numpy import average


class InternalEvaluation(object):
    """This a class for internal evaluation: validating cluster model without known ground truth.
    """
    @staticmethod
    def __get_node_distance(graph, node, neighbors, mode=''):
        """Get distance from a node to its neighbor.

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
        mode        : str
            Mode of measurement, i.e., min, max, avg

        Returns
        -------
        final_distance    : float
            The average distance of node to its analyzed neighbors.
        """
        neigbors_weight = graph[node]
        distance = []
        final_distance = 0.
        for node_id, weight in neigbors_weight.iteritems():
            if node_id in neighbors:
                distance.append(1 - weight[0]['weight'])
            else:
                continue

        # if list is empty
        if not distance:
            distance.append(0)

        # check for mode
        if mode == 'min':
            final_distance = min(distance)
        elif mode == 'max':
            final_distance = max(distance)
        elif mode == 'avg':
            final_distance = average(distance)

        final_distance = round(final_distance, 5)
        return final_distance

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
        cid = set(clusters.keys())
        intracluster_avg, intercluster_avg, node_silhouttes = {}, {}, {}

        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                node_silhouttes[cluster[0]] = 1
            else:
                # get average of intra-cluster distance
                for node in cluster:
                    intracluster_avg[node] = InternalEvaluation.__get_node_distance(graph, node, cluster, 'avg')

                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for node in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        temp_distance = InternalEvaluation.__get_node_distance(graph, node,
                                                                               intercluster_nodes[neighbor], 'avg')
                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_avg[node] = min(distance.values()) if len(distance.keys()) > 0 else 0.

                # get vertex silhoutte
                for node in cluster:
                    try:
                        node_silhouttes[node] = (intercluster_avg[node] - intracluster_avg[node]) / \
                                                max(intercluster_avg[node], intracluster_avg[node])
                    except ZeroDivisionError:
                        node_silhouttes[node] = 0.

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
        """Get silhoutte index for a graph [Almeida2011]_.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        silhoutte_index : float
            The silhoutte index for a graph.

        References
        ----------
        .. [Almeida2011] Helio Almeida, Dorgival Guedes, Wagner Meira Jr, and Mohammed J. Zaki.
                         "Is there a best quality metric for graph clusters?."
                         In Joint European Conference on Machine Learning and Knowledge Discovery in Databases,
                         pp. 44-59. Springer Berlin Heidelberg, 2011.
        """
        cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(graph, clusters)
        silhoutte_index = average(cluster_silhouttes.values())

        return silhoutte_index

    @staticmethod
    def __get_compactness(graph, clusters):
        """Maximum node distance as diameter to show a compactness of a cluster.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        final_compactness   : float
            Diameter or compactness of a cluster.
        """
        compactness = {}
        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                compactness[cluster[0]] = 0.
            else:
                for node in cluster:
                    compactness[node] = InternalEvaluation.__get_node_distance(graph, node, cluster, 'max')

        final_compactness = max(compactness)
        return final_compactness

    @staticmethod
    def __get_separation(graph, clusters):
        """Separation or minimum distance between clusters.

        It is actually minimum distance between two nodes in calculated clusters.
        Then, we find the most minimum one for all clusters.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        separation  : float
            Minimum distance between all clusters.
        """
        cid = set(clusters.keys())
        intercluster_distance = {}
        separation = 1.
        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                separation = 0.
            else:
                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for node in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        temp_distance = InternalEvaluation.__get_node_distance(graph, node,
                                                                               intercluster_nodes[neighbor], 'min')
                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_distance[node] = min(distance.values()) if len(distance.keys()) > 0 else 0.

                    # get minimum intercluster distance
                    if intercluster_distance[node] < separation:
                        separation = intercluster_distance[node]

        return separation

    @staticmethod
    def get_dunn_index(graph, clusters):
        """Get Dunn index. The basic formula is separation / compactness [Liu2010]_.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.

        Returns
        -------
        dunn_index  : float
            Dunn index value.

        References
        ----------
        .. [Liu2010] Liu, Y., Li, Z., Xiong, H., Gao, X., & Wu, J. Understanding of internal clustering
                     validation measures. In 2010 IEEE 10th International Conference on Data Mining, pp. 911-916.
        """
        dunn_index = \
            InternalEvaluation.__get_separation(graph, clusters) / InternalEvaluation.__get_compactness(graph, clusters)
        return dunn_index
