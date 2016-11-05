from itertools import combinations


class ClusterUtility(object):
    """A class contains some utilities to do clustering algorithm.
    """
    @staticmethod
    def get_geometric_mean(weights):
        """Get geometric mean or intensity in a clique. A clique can be a k-clique or maximal clique.

        Parameters
        ----------
        weights : list[float]
            List of edge weight in a clique.

        Returns
        -------
        gmean   : float
            Geometric mean of given edge weights.
        """
        multiplication = 1
        for weight in weights:
            multiplication *= weight

        gmean = 0.0
        if multiplication > 0.0:
            k = float(len(weights))
            gmean = multiplication ** (1 / k)

        gmean = round(gmean, 5)
        return gmean

    @staticmethod
    def get_weighted_cliques(graph, cliques, threshold):
        """Get weighted cliques based on given intensity threshold.

        A clique which its weight are less then threshold is omiited.
        This procedure will filter unsignificant cliques.

        Parameters
        ----------
        graph       : graph
            A graph to check for its weighted cliques.
        cliques     : list[frozenset]
            List of clique list found.
        threshold   : float
            Intensity (geometric mean) threshold.

        Returns
        -------
        weighted_cliques    : list[list]
            List of clique with significant weight.
        """
        weighted_kcliques = []
        for clique in cliques:
            weights = []
            for u, v in combinations(clique, 2):
                reduced_precision = round(graph[u][v][0]['weight'], 5)
                weights.append(reduced_precision)
            gmean = ClusterUtility.get_geometric_mean(weights)

            if gmean > threshold:
                weighted_kcliques.append(frozenset(clique))

        return weighted_kcliques

    @staticmethod
    def set_cluster_id(graph, clusters):
        """Set incremental cluster identifier start from 0.

        Parameters
        ----------
        graph       : graph
            Graph to be set for its cluster id.
        clusters    : dict[list]
            Dictionary contains list of node in a particular cluster.
        """
        for cluster_id, cluster in clusters.iteritems():
            for node in cluster:
                graph.node[node]['cluster'] = cluster_id

    @staticmethod
    def get_cluster_property(graph, clusters):
        """Get cluster property.

        Parameters
        ----------
        graph       : graph
            Graph to be analyzed.
        clusters    : dict[list]
            Dictionary contains sequence of nodes in all clusters.

        Returns
        -------
        cluster_property    : dict
            Property of a cluster. For example: frequency of event logs.
        """
        cluster_property = {}      # event log frequency per cluster
        for cluster_id, nodes in clusters.iteritems():
            properties = {}
            for node_id in nodes:
                properties['frequency'] = properties.get('frequency', 0) + graph.node[node_id]['frequency']
            cluster_property[cluster_id] = properties

        return cluster_property
