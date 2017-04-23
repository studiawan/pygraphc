import networkx as nx
from itertools import combinations
from KCliquePercolation import KCliquePercolation
from ClusterUtility import ClusterUtility


class MaxCliquesPercolation(KCliquePercolation):
    """This class find maximal cliques and their percolation in a graph.

    The procedure will find any intersection (percolation) between any maximal cliques found.
    The cluster is defined as percolated maximal cliques [Reid2012]_.

    References
    ----------
    .. [Reid2012] Fergal Reid, Aaron McDaid, and Neil Hurley. Percolation computation in complex networks.
                  In Proceedings of the 2012 IEEE/ACM International Conference on Advances in Social Networks
                  Analysis and Mining, pp. 274-281, 2012.
    """
    def __init__(self, graph, edges_weight, nodes_id):
        """This is the constructor of class MaxCliquesPercolation

        Parameters
        ----------
        graph           : graph
            Graph to be clustered.
        edges_weight    : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id        : list
            List of all node identifier.

        Notes
        -----
        max_cliques : list[frozenset]
            List of frozenset containing node id for each maximal clique.
        """
        super(MaxCliquesPercolation, self).__init__(graph, edges_weight, nodes_id)

    def init_maxclique_percolation(self):
        """Initialization of maxial clique percolation method.

        The first step is to build temporary graph (percolation graph). Then the procedure finds
        all maximal cliques in the graph.
        """
        super(MaxCliquesPercolation, self)._build_temp_graph()
        maxcliques = self._find_maxcliques()
        self.cliques = maxcliques

    def get_maxcliques_percolation(self, k):
        """The main method to find clusters based on maximal clique percolation.

        This method looks for percolation between cliques.
        It then remove any edges that connecting two vertices but has different clusters.

        Returns
        -------
        k           : int
            Number of percolation or intersection between an individual clique.
        clusters    : dict[frozenset]
            List of frozenset containing node identifier (node id in integer).
        """
        super(MaxCliquesPercolation, self)._get_percolation_graph(self.cliques, k)
        super(MaxCliquesPercolation, self)._remove_outcluster()
        clusters = super(MaxCliquesPercolation, self)._get_clusters()

        return clusters

    def _find_maxcliques(self):
        """Find maximal cliques using `find_clique` function from NetworkX.

        Returns
        -------
        maxcliques  : list[frozenset]
            List of frozenset containing node id for each maximal clique.
        """
        maxcliques = list(frozenset(c) for c in nx.find_cliques(self.graph))
        self.cliques = maxcliques
        return maxcliques


class MaxCliquesPercolationWeighted(MaxCliquesPercolation):
    """This is a class for maximal clique percolation with edge weight [Liu2009]_.

    Edge weight is evaluated using intensity threshold or the geometric mean
    for all edge weights in a maximal clique [Studiawan2016c]_. We then remove the overlapping nodes
    where a node only follow the weighter neighboring cluster [Studiawan2016c]_.

    References
    ----------
    .. [Liu2009]        Guimei Liu, Limsoon Wong, and Hon Nian Chua. Complex discovery from
                        weighted PPI networks. Bioinformatics, 25(15):1891-1897, 2009.
    .. [Studiawan2016c] H. Studiawan, C. Payne, F. Sohel, SSH log clustering using weighted
                        maximal clique percolation (to be submitted).
    """
    def __init__(self, graph, edges_weight, nodes_id):
        """This is the constructor of class MaxCliquePercolation Weighted.

        The parameters are the same with its parent class but we add a threshold
        for the intensity for maximal clique found.

        Parameters
        ----------
        graph           : graph
            Graph to be clustered.
        edges_weight    : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id        : list
            List of all node identifier.
        """
        super(MaxCliquesPercolationWeighted, self).__init__(graph, edges_weight, nodes_id)
        self.percolation_dict = {}

    def get_maxcliques_percolation_weighted(self, k, threshold):
        """This is the main method for maximal clique percolation for edge-weighted graph.

        Parameters
        ----------
        k           : int
            Number of percolation or intersection between an individual clique.
        threshold   : float
            Threshold for intensity of maximal clique.

        Returns
        -------
        clusters    : dict[int, frozenset]
            List of frozenset containing node identifier (node id in integer).

        Notes
        -----
        weighted_maxcliques : list[frozenset]
            List of frozenset containing node identifier for each weighted maximal clique.
        """
        # get weighted maximal cliques and get percolation
        weighted_maxcliques = ClusterUtility.get_weighted_cliques(self.graph, self.cliques, threshold)
        clusters = {}
        if weighted_maxcliques:
            super(MaxCliquesPercolationWeighted, self)._get_percolation_graph(weighted_maxcliques, k)
            self.__set_percolation_dict(self.clique_percolation)

            # remove overlapping nodes
            percolations = self.clique_percolation.values()
            for p1, p2 in combinations(percolations, 2):
                intersections = p1.intersection(p2)
                if intersections:
                    for node in intersections:
                        node_neighbors = self.graph.neighbors(node)
                        p1_neighbors, p2_neighbors = p1.intersection(node_neighbors), p2.intersection(node_neighbors)
                        p1_neighbors_weight = self.__get_neighbors_weight(node, p1_neighbors)
                        p2_neighbors_weight = self.__get_neighbors_weight(node, p2_neighbors)

                        # follow the neighboring cluster which has bigger sum of edge-weight
                        self.percolation_dict[node] = self.percolation_dict[list(p1_neighbors)[0]] \
                            if p1_neighbors_weight > p2_neighbors_weight else \
                            self.percolation_dict[list(p2_neighbors)[0]]

            self.__set_graph_cluster()
            clusters = self.__get_clusters()

        # remove intracluster edges
        super(MaxCliquesPercolationWeighted, self)._remove_outcluster()
        return clusters

    def __set_percolation_dict(self, percolations):
        """Set dictionary of node id and its index in percolations.

        Parameters
        ----------
        percolations    : dict[frozenset]
            Dictionary of frozenset containing nodes id for each maximal clique.
        """
        nodes = self.graph.nodes()
        percolations_merged = []
        for index, percolation in percolations.iteritems():
            for p in percolation:
                self.percolation_dict[p] = index

            # merge percolations list
            percolations_merged += percolation

        diff = set(nodes).difference(percolations_merged)
        other_cluster = len(percolations)
        if diff:
            for i in diff:
                self.percolation_dict[i] = other_cluster
                other_cluster += 1

    def __get_neighbors_weight(self, node, neighbors):
        """Get all weight of neighboring cluster.

        Parameters
        ----------
        node        : int
            Node identifier
        neighbors   : list[int]
            List of node identifier of intersection between two clusters

        Returns
        -------
        weight  : int
            Sum of all edge weight from specific neighboring cluster.
        """
        weight = 0
        for n in neighbors:
            weight += self.graph[node][n][0]['weight']

        return weight

    def __set_graph_cluster(self):
        """Set cluster id in the given graph based on percolation dictionary.

        Returns
        -------
        self.graph  : graph
            Graph with updated cluster identifier after cluster processing.
        """
        for node in self.graph.nodes_iter(data=True):
            self.graph.node[node[0]]['cluster'] = self.percolation_dict[node[0]]
        return self.graph
    
    def __get_clusters(self):
        """Get maximal clique percolation as clusters with incremental cluster id.

        Returns
        -------
        clusters    : dict[list]
            Dictionary of list containing node identifier for each cluster found.
        """
        cluster_ids = set(self.percolation_dict.values())
        clusters = {}
        cluster_idx = 0
        for ids in cluster_ids:
            cluster = []
            for node, cluster_id in self.percolation_dict.iteritems():
                if ids == cluster_id:
                    cluster.append(node)
            clusters[cluster_idx] = cluster
            cluster_idx += 1

        return clusters
