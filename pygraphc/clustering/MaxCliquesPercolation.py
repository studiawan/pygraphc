import networkx as nx
from itertools import combinations
from KCliquePercolation import KCliquePercolation
from ClusterUtility import ClusterUtility


class MaxCliquesPercolation(KCliquePercolation):
    """This class find maximal cliques and their percolation in a graph.

    The procedure will find any intersection (percolation) between any maximal cliques found.
    The cluster is defined as percolated maximal cliques.

    References
    ----------
    .. [1] Guimei Liu, Limsoon Wong, and Hon Nian Chua. Complex discovery from weighted PPI networks.
           Bioinformatics, 25(15):1891-1897, 2009.
    .. [2] Fergal Reid, Aaron McDaid, and Neil Hurley. Percolation computation in complex networks.
           In Proceedings of the 2012 IEEE/ACM International Conference on Advances in Social Networks
           Analysis and Mining, pp. 274-281, 2012.
    """
    def __init__(self, graph, edges_weight, nodes_id, k):
        """This is the constructor of class MaxCliquesPercolation

        Parameters
        ----------
        graph           : graph
            Graph to be clustered.
        edges_weight    : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id        : list
            List of all node identifier.
        k               : int
            Number of percolation or intersection between an individual clique.
        """
        super(MaxCliquesPercolation, self).__init__(graph, edges_weight, nodes_id, k)
        self.max_cliques = None

    def get_maxcliques_percolation(self):
        """The main method to find clusters based on maximal clique percolation.

        The first step is to build temporary graph (percolation graph). Then the procedure finds
        all maximal cliques in the graph. Next, it looks for percolation between cliques.
        This method then remove any edges that connecting two vertices but has different clusters.

        Returns
        -------
        clusters    : list[frozenset]
            List of frozenset containing node identifier (node id in integer).

        """
        print 'get_maxcliques_percolation ...'
        super(MaxCliquesPercolation, self)._build_temp_graph()
        maxcliques = self._find_maxcliques()

        super(MaxCliquesPercolation, self)._get_percolation_graph(maxcliques)
        super(MaxCliquesPercolation, self)._remove_outcluster()
        clusters = super(MaxCliquesPercolation, self)._get_clusters()

        return clusters

    def get_maxcliques(self):
        """Get enumerated maximal cliques.

        Returns
        -------
        max_cliques : list[frozenset]
            List of frozenset containing node id for each maximal clique.
        """
        return self.max_cliques

    def _find_maxcliques(self):
        """Find maximal cliques using `find_clique` function from NetworkX.

        Returns
        -------
        maxcliques  : list[frozenset]
            List of frozenset containing node id for each maximal clique.
        """
        maxcliques = list(frozenset(c) for c in nx.find_cliques(self.graph) if len(c) >= self.k)
        self.max_cliques = maxcliques
        return maxcliques


class MaxCliquesPercolationWeighted(MaxCliquesPercolation):
    def __init__(self, graph, edges_weight, nodes_id, k, threshold):
        super(MaxCliquesPercolationWeighted, self).__init__(graph, edges_weight, nodes_id, k)
        self.threshold = threshold
        self.percolation_dict = {}

    def get_maxcliques_percolation_weighted(self):
        maxcliques = self._find_maxcliques()
        super(MaxCliquesPercolationWeighted, self)._get_percolation_graph(maxcliques)
        percolations = super(MaxCliquesPercolationWeighted, self).get_clique_percolation()
        self.__set_percolation_dict(percolations)
        for p1, p2 in combinations(percolations, 2):
            intersections = p1.intersection(p2)
            if intersections:
                for node in intersections:
                    node_neighbors = self.graph.neighbors(node)
                    p1_neighbors, p2_neighbors = p1.intersection(node_neighbors), p2.intersection(node_neighbors)
                    p1_neighbors_weight = self.__get_neighbors_weight(node, p1_neighbors)
                    p2_neighbors_weight = self.__get_neighbors_weight(node, p2_neighbors)

                    self.percolation_dict[node] = self.percolation_dict[list(p1_neighbors)[0]] \
                        if p1_neighbors_weight > p2_neighbors_weight else self.percolation_dict[list(p2_neighbors)[0]]

        self.__set_graph_cluster()
        clusters = self.__get_clusters()
        return clusters

    def _find_maxcliques(self):
        maxcliques = super(MaxCliquesPercolationWeighted, self)._find_maxcliques()
        weighted_maxcliques = ClusterUtility.get_weighted_cliques(self.graph, maxcliques, self.threshold)
        self.max_cliques = weighted_maxcliques

        return weighted_maxcliques

    def __set_percolation_dict(self, percolations):
        nodes = self.graph.nodes()
        percolations_merged = []
        for index, percolation in enumerate(percolations):
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
        weight = 0
        for n in neighbors:
            weight += self.graph[node][n][0]['weight']

        return weight

    def __set_graph_cluster(self):
        for node in self.graph.nodes_iter(data=True):
            self.graph.node[node[0]]['cluster'] = self.percolation_dict[node[0]]
        return self.graph
    
    def __get_clusters(self):
        cluster_ids = set(self.percolation_dict.values())
        clusters = []
        for ids in cluster_ids:
            cluster = []
            for node, cluster_id in self.percolation_dict.iteritems():
                if ids == cluster_id:
                    cluster.append(node)
            clusters.append(cluster)

        return clusters
