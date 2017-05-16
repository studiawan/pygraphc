import numpy as np


class InternalEvaluation(object):
    """This a class for internal evaluation: validating cluster model without known ground truth.
    """
    @staticmethod
    def __get_node_distance(nodex, neighbors, measurement, mode, graph=None, cosine_similarity=None):
        """Get distance from a node to its neighbor.

        The neighbors can be located in intra-cluster or inter-cluster. The distance means
        edge weight in the graph case. In non-graph clustering method, node is equal with log line id.

        Parameters
        ----------
        nodex               : int
            Node identifier or log line identifier in incremental integer.
        neighbors           : list
            List of neighbors' node identifier.
        measurement         : str
            Mode of measurement, i.e., min, max, avg.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

        Returns
        -------
        final_distance  : float
            The average distance of node to its analyzed neighbors.
        """
        distances = []
        final_distance = 0.
        if mode == 'graph':
            neigbors_weight = graph[nodex]
            for node_id, weight in neigbors_weight.iteritems():
                if node_id in neighbors:
                    distances.append(1 - weight[0]['weight'])

            # if list is empty
            if not distances:
                distances.append(0.)

        elif mode == 'text':
            for neighbor in neighbors:
                if nodex != neighbor:
                    try:
                        distance = cosine_similarity[(nodex, neighbor)]
                    except KeyError:
                        distance = cosine_similarity[(neighbor, nodex)]
                    distances.append(1 - distance)

        # check for mode
        if mode == 'text' or mode == 'graph':
            if distances:
                if measurement == 'min':
                    final_distance = min(distances)
                elif measurement == 'max':
                    final_distance = max(distances)
                elif measurement == 'avg':
                    final_distance = np.average(distances)
                del distances[:]

        final_distance = round(final_distance, 3)
        return final_distance

    @staticmethod
    def __get_node_silhoutte(clusters, mode, graph=None, cosine_similarity=None):
        """Get node silhoutte.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

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
                for nodex in cluster:
                    if mode == 'graph':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         graph)
                    elif mode == 'text':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         None, cosine_similarity)

                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for nodex in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        if mode == 'graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, graph)
                        elif mode == 'text':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, None, cosine_similarity)
                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_avg[nodex] = min(distance.values()) if len(distance.keys()) > 0 else 0.

                # get vertex silhoutte
                for nodex in cluster:
                    try:
                        node_silhouttes[nodex] = (intercluster_avg[nodex] - intracluster_avg[nodex]) / \
                                                 max(intercluster_avg[nodex], intracluster_avg[nodex])
                    except ZeroDivisionError:
                        node_silhouttes[nodex] = 0.

        return node_silhouttes

    @staticmethod
    def __get_cluster_silhoutte(clusters, mode, graph=None, cosine_similarity=None):
        """Get cluster silhoutte.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

        Returns
        -------
        cluster_silhouttes  : dict[int, float]
            A dictionary containing silhoutte per cluster. Key: cluster identifier, value: silhoutte.
        """
        node_silhouttes, cluster_silhouttes = {}, {}
        if mode == 'graph':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, graph)
        elif mode == 'text':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, None, cosine_similarity)

        for cluster_id, cluster in clusters.iteritems():
            silhoutte = []
            for nodex in cluster:
                silhoutte.append(node_silhouttes[nodex])
            cluster_silhouttes[cluster_id] = np.average(silhoutte) if silhoutte else -1.

        return cluster_silhouttes

    @staticmethod
    def get_silhoutte_index(clusters, mode, graph=None, cosine_similarity=None):
        """Get silhoutte index for a graph [Almeida2011]_.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

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
        cluster_silhouttes = {}
        if mode == 'graph':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, graph)
        elif mode == 'text':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, None, cosine_similarity)

        silhoutte_index = np.average(cluster_silhouttes.values()) if cluster_silhouttes else -1.
        return silhoutte_index

    @staticmethod
    def __get_compactness(clusters, mode, graph=None, cosine_similarity=None):
        """Maximum node distance as diameter to show a compactness of a cluster.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

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
                for nodex in cluster:
                    if mode == 'graph':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, graph)
                    elif mode == 'text':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, None,
                                                                                    cosine_similarity)
        final_compactness = max(compactness.values()) if compactness else 0.
        return final_compactness

    @staticmethod
    def __get_separation(clusters, mode, graph=None, cosine_similarity=None):
        """Separation or minimum distance between clusters.

        It is actually minimum distance between two nodes in calculated clusters.
        Then, we find the most minimum one for all clusters.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

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
                if separation <= 1.:
                    pass
            else:
                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for nodex in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        if mode == 'graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, graph)
                        elif mode == 'text':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, None, cosine_similarity)
                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_distance[nodex] = min(distance.values()) if len(distance.keys()) > 0 else 1.

                    # get minimum intercluster distance
                    if intercluster_distance[nodex] < separation:
                        separation = intercluster_distance[nodex]

        return separation

    @staticmethod
    def get_dunn_index(clusters, mode, graph=None, cosine_similarity=None):
        """Get Dunn index. The basic formula is separation / compactness [Liu2010]_.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.

        Returns
        -------
        dunn_index  : float
            Dunn index value.

        References
        ----------
        .. [Liu2010] Liu, Y., Li, Z., Xiong, H., Gao, X., & Wu, J. Understanding of internal clustering
                     validation measures. In 2010 IEEE 10th International Conference on Data Mining, pp. 911-916.
        """
        dunn_index = 0.
        if mode == 'graph':
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, graph) / \
                             InternalEvaluation.__get_compactness(clusters, mode, graph)
            except ZeroDivisionError:
                dunn_index = 0.
        elif mode == 'text':
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, None, cosine_similarity) / \
                             InternalEvaluation.__get_compactness(clusters, mode, None, cosine_similarity)
            except ZeroDivisionError:
                dunn_index = 0.

        return dunn_index
