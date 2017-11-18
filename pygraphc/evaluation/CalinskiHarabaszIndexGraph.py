import networkx as nx
from random import choice


class CalinskiHarabaszIndex(object):
    """A class to calculate Calinski-Harabasz Index [Calinski1974]_. We use the terms for this index from [Maulik2002]_.

    References
    ----------
    .. [Calinski1974] Calinski, T., & Harabasz, J. A dendrite method for cluster analysis.
                      Communications in Statistics-theory and Methods, 3(1), 1-27, 1974.
    .. [Maulik2002]   Maulik, U., & Bandyopadhyay, S. Performance evaluation of some clustering algorithms
                      and validity indices. IEEE Transactions on Pattern Analysis and Machine Intelligence, 24(12),
                      1650-1654, 2002.
    """
    def __init__(self, graph, clusters):
        """Constructor for CalinskiHarabaszIndex class.

        Parameters
        ----------
        graph       : graph
            A graph to be evaluated.
        clusters    : dict
            Dictionary containing the cluster data. Key: cluster id, value: list of nodes.
        """
        self.graph = graph
        self.clusters = clusters
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
        self.total_nodes = 0

        # get cluster properties: centroid per cluster, total nodes per cluster
        self.__get_all_cluster_properties()

    def __get_centroid(self, cluster=None):
        """Get the centroid of a cluster in the graph or the centroid of the graph.

        Parameters
        ----------
        cluster : list
            Nodes list of a cluster.

        Returns
        -------
        centroid_node   : int
            Centroid node of a cluster.
        """
        # centroid of a cluster
        if cluster:
            subgraph = self.graph.subgraph(cluster)
            centroid = nx.center(subgraph)
        # centroid of the graph
        else:
            centroid = nx.center(self.graph)

        # choose randomly if more than one centroid found
        centroid_node = choice(centroid) if len(centroid) > 1 else centroid
        return centroid_node

    def __get_all_cluster_properties(self):
        """Get cluster properties, i.e., centroid, total nodes per cluster, and total nodes in a graph.
        """
        for cluster_id, nodes in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(nodes)
            self.cluster_total_nodes[cluster_id] = len(nodes)
        self.total_nodes = self.graph.number_of_nodes()

    def __get_distance(self, source, dest):
        """Get distance from source to destination using Dijkstra algorithm.

        Parameters
        ----------
        source  : int
            Source node.
        dest    : int
            Destination node.

        Returns
        -------
        distance    : float
            Distance from source node to destination node.
        """
        try:
            distance = nx.dijkstra_path_length(self.graph, source, dest)
        except nx.NetworkXNoPath:
            distance = 0.

        return distance

    def __get_trace_b(self):
        """Get trace B, trace between cluster, as described in [Maulik2002]_.

        Returns
        -------
        total_trace_b   : float
            Trace B value.
        """
        traces_b = []
        graph_centroid = self.__get_centroid()
        for cluster_id, nodes in self.clusters.iteritems():
            trace_b = self.cluster_total_nodes[cluster_id] * \
                      (self.__get_distance(self.cluster_centroids[cluster_id], graph_centroid) ** 2)
            traces_b.append(trace_b)

        total_trace_b = sum(traces_b)
        return total_trace_b

    def __get_trace_w(self):
        """Get trace W, trace within cluster, as described in [Maulik2002]_.

        Returns
        -------
        total_traces_w  : float
            Trace W value.
        """
        traces_w = []
        for cluster_id, nodes in self.clusters.iteritems():
            trace_w_cluster = []
            for node in nodes:
                trace_w = self.__get_distance(node, self.cluster_centroids[cluster_id]) ** 2
                trace_w_cluster.append(trace_w)
            traces_w.append(sum(trace_w_cluster))

        total_traces_w = sum(traces_w)
        return total_traces_w

    def get_calinski_harabasz(self):
        """Get Calinski-Harabasz index.

        Returns
        -------
        ch_index    : float
            Calinski-Harabasz index.
        """
        total_cluster = len(self.clusters.keys())
        ch_index = (self.__get_trace_b() / (total_cluster - 1)) / \
                   (self.__get_trace_w() / (self.total_nodes - total_cluster))

        return ch_index
