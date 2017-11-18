import networkx as nx
from random import choice
from itertools import combinations, product


class DaviesBouldinIndex(object):
    """A class to calculate Davies-Bouldin index [Davies1979]_. We use the terms for this index from [Kovacs2005]_.

    References
    ----------
    .. [Davies1979] Davies, D. L., & Bouldin, D. W. A cluster separation measure.
                    IEEE Transactions on Pattern Analysis and Machine Intelligence, (2), 224-227, 1979.
    .. [Kovacs2005] Kovacs, F., Legany, C., & Babos, A. Cluster validity measurement techniques.
                    In 6th International Symposium of Hungarian Researchers on Computational Intelligence, 2005.
    """
    def __init__(self, graph, clusters):
        """Constructor for DaviesBouldinIndex class.

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
        self.total_cluster = 0
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
        # get cluster centroid and cluster total nodes
        for cluster_id, nodes in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(nodes)
            self.cluster_total_nodes[cluster_id] = len(nodes)
        self.total_cluster = len(self.clusters.keys())
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
        # get distance from source to destination
        try:
            distance = nx.dijkstra_path_length(self.graph, source, dest)
        except nx.NetworkXNoPath:
            distance = 0.

        return distance

    def __get_dispersion(self):
        """Get dispersion measure of a cluster (s). It is actually a within-cluster or intra-cluster similarity measure.

        Returns
        -------
        cluster_dispersions : dict
            Cluster dispersion. Key: cluster id, value: dispersion.
        """
        cluster_dispersions = {}
        for cluster_id, nodes in self.clusters.iteritems():
            distances = []
            for node in nodes:
                distance = self.__get_distance(node, self.cluster_centroids[cluster_id])
                distances.append(distance)
            total_distance = sum(distances)
            cluster_dispersions[cluster_id] = 1 / self.cluster_total_nodes[cluster_id] * total_distance

        return cluster_dispersions

    def __get_dissimilarity(self):
        """Get cluster dissimilarity measure (d). It is actually a between-cluster or inter-cluster similarity measure.

        Returns
        -------
        cluster_dissimilarity   : dict
            Cluster dissimilarity. Key: cluster id, value: dissimilarity.
        """
        cluster_dissimilarity = {}
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            cluster_dissimilarity[(cluster_id1, cluster_id2)] = self.__get_distance(self.cluster_centroids[cluster_id1],
                                                                                    self.cluster_centroids[cluster_id2])
        return cluster_dissimilarity

    def __get_similarity(self):
        """Get similarity measure of all clusters (R_ij).

        Returns
        -------
        similarity  : dict
            Cluster similarity. Key: cluster id, value: similarity.
        """
        similarity = {}
        cluster_dispersions = self.__get_dispersion()
        cluster_dissimilarity = self.__get_dissimilarity()
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            similarity[(cluster_id1, cluster_id2)] = \
                cluster_dispersions[cluster_id1] + cluster_dispersions[cluster_id2] / \
                cluster_dissimilarity[(cluster_id1, cluster_id2)]

        return similarity

    def __get_r(self):
        """Get maximum similarity measure for each cluster.

        Returns
        -------
        r   : dict
            Maximum similarity value for each cluster. Key: cluster_id, value: maximum similarity.
        """
        r = {}
        similarity = self.__get_similarity()
        similarity_keys = similarity.keys()
        for cluster_id, nodes in self.clusters.iteritems():
            r_cluster = []
            for cluster_id1, cluster_id2 in product(xrange(self.total_cluster), repeat=2):
                if cluster_id == cluster_id1:
                    if (cluster_id1, cluster_id2) in similarity_keys:
                        r_cluster.append(similarity[(cluster_id1, cluster_id2)])
                    else:
                        r_cluster.append(similarity[(cluster_id2, cluster_id1)])
            r[cluster_id] = max(r_cluster)

        return r

    def get_davies_bouldin(self):
        """Get Davies-Bouldin index.

        Returns
        -------
        db_index    : float
            Davies-Bouldin index.
        """
        r = self.__get_r()
        db_index = 1 / self.total_cluster * sum(r.values())

        return db_index
