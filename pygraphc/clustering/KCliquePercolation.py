import networkx as nx
from collections import deque
from itertools import chain, islice, combinations
from ClusterUtility import ClusterUtility


class KCliquePercolation(object):
    """This is a class for graph clustering based on k-clique percolation [1]_.

    The procedure will find k-clique. If there is any percolation between k-cliques, it will be set as a cluster.
    The unnecessary edges will be removed. The use of this method for event log clustering was presented in [2]_.

    References
    ----------
    .. [1] I. J. Farkas, D. Abel, G. Palla, and T. Vicsek, Weighted network modules,
           New Journal of Physics, 9(6), p. 180, 2007.
    .. [2] H. Studiawan, B. A. Pratomo, and R. Anggoro, Clustering of SSH brute-force attack logs using
           k-clique percolation, in Proceedings of the 10th International Conference on Information Communication
           Technology and Systems, pp. 33-36, 2016.
    """
    def __init__(self, graph, edges_weight, nodes_id, k):
        """This is a constructor for class KCliquePercolation.

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
        print 'kclique_percolation: initialization ...'
        self.graph = graph
        self.edges_weight = edges_weight
        self.nodes_id = nodes_id
        self.k = k
        self.g = None
        self.percolated_nodes = []
        self.removed_edges = []
        self.clique_percolation = {}

    def get_percolation_nodes(self):
        """Get percolation nodes after finished clustering.

        Returns
        -------
        percolated_nodes    : list
            List of all percolated nodes
        """
        return self.percolated_nodes

    def get_removed_edges(self):
        """Get removed edges after clustering process.

        Returns
        -------
            removed_edges   : list[tuple]
                List of tuple containing edge from (node1, node2)
        """
        return self.removed_edges

    def get_clique_percolation(self):
        """Get all cluster in percolation (temporary) graph.

        Returns
        -------
        clique_percolation  : dict[frozenset]
            Dictionary of nodes in each cluster in frozenset.
        """
        return self.clique_percolation

    def get_kclique_percolation(self):
        """This is the main method to call all k-clique percolation clustering.

        Returns
        -------
        clusters    : dict[list]
            List of list containing nodes identifier for each cluster.
        """
        print 'get_kclique_percolation ...'
        self._build_temp_graph()
        kcliques = self._find_kcliques()
        self._get_percolation_graph(kcliques)
        self._remove_outcluster()
        clusters = self._get_clusters()

        return clusters

    def _find_kcliques(self):
        """Find all k-cliques in a graph.

        Returns
        -------
        kcliques    : list[frozenset]
            List of k-cliques found but only return specified k. The frozenset contains nodes identifier.
        """
        k_cliques = list(self._enumerate_all_cliques())
        kcliques = [frozenset(clique) for clique in k_cliques if len(clique) == self.k]

        return kcliques

    def _build_temp_graph(self):
        """Build a temporary graph to get a percolation between individual k-clique.
        """
        self.g = nx.Graph()
        self.g.add_nodes_from(self.nodes_id)
        self.g.add_weighted_edges_from(self.edges_weight)

    def _enumerate_all_cliques(self):
        """Returns all cliques in an undirected graph.

        This method returns cliques of size (cardinality)
        k = 1, 2, 3, ..., maxDegree - 1. Where maxDegree is the maximal
        degree of any node in the graph.

        Returns
        -------
        generator of lists: generator of list for each clique.

        Notes
        -----
        Based on the algorithm published by Zhang et al. (2005) [1]_
        and adapted to output all cliques discovered.
        This algorithm is not applicable on directed graphs.
        This algorithm ignores self-loops and parallel edges as
        clique is not conventionally defined with such edges.
        There are often many cliques in graphs.
        This algorithm however, hopefully, does not run out of memory
        since it only keeps candidate sublists in memory and
        continuously removes exhausted sublists.

        The original source code is taken from NetworkX development branch [2]_.

        References
        ----------
        .. [1] Yun Zhang, Abu-Khzam, F.N., Baldwin, N.E., Chesler, E.J.,
               Langston, M.A., Samatova, N.F.,
               Genome-Scale Computational Approaches to Memory-Intensive
               Applications in Systems Biology.
               Supercomputing, 2005. Proceedings of the ACM/IEEE SC 2005
               Conference, pp. 12, 12-18 Nov. 2005.
               doi: 10.1109/SC.2005.29.
               http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1559964&isnumber=33129
        .. [2] Dan Schult, Source code for networkx.algorithms.clique.
               https://networkx.github.io/documentation/development/_modules/networkx/algorithms/clique.html
        """

        print 'enumerate_all_cliques ...'
        index = {}
        nbrs = {}
        for u in self.g:
            index[u] = len(index)
            # Neighbors of u that appear after u in the iteration order of G.
            nbrs[u] = {v for v in self.g[u] if v not in index}

        queue = deque(([u], sorted(nbrs[u], key=index.__getitem__)) for u in self.g)
        # Loop invariants:
        # 1. len(base) is nondecreasing.
        # 2. (base + cnbrs) is sorted with respect to the iteration order of G.
        # 3. cnbrs is a set of common neighbors of nodes in base.
        while queue:
            base, cnbrs = map(list, queue.popleft())
            yield base
            for i, u in enumerate(cnbrs):
                # Use generators to reduce memory consumption.
                queue.append((chain(base, [u]),
                              filter(nbrs[u].__contains__,
                                     islice(cnbrs, i + 1, None))))

    def _get_percolation_graph(self, kcliques):
        """Get percolation graph.

        This temporary graph also well known as percolation graph in the literatures. A node represents a k-clique
        and an edge will be drawn if there is any intersection between two k-cliques.

        Parameters
        ----------
        kcliques    : list[frozenset]
            List of all k-cliques found with user-specified k.
        """
        percolation_graph = nx.Graph()
        percolation_graph.add_nodes_from(kcliques)

        # Add an edge in the percolation graph for each pair of cliques that percolate
        for clique1, clique2 in combinations(kcliques, 2):
            percolation = clique1.intersection(clique2)
            self.percolated_nodes.append(percolation)
            if len(percolation) >= (self.k - 1):
                percolation_graph.add_edge(clique1, clique2)

        # Get all connected component in percolation graph
        cluster_id = 0
        for component in nx.connected_components(percolation_graph):
            self.clique_percolation[cluster_id] = frozenset.union(*component)
            cluster_id += 1

        # set cluster id
        ClusterUtility.set_cluster_id(self.graph, self.clique_percolation)

    def _remove_outcluster(self):
        """Remove edges that connect to other clusters.

        This method will first find any edges in the cluster member. If edges connecting to a node does not belong to
        the current cluster, then it will be removed.
        """
        # remove edge outside cluster
        for node in self.g.nodes_iter(data=True):
            neighbors = self.g.neighbors(node[0])
            for neighbor in neighbors:
                # if cluster id of current node is not the same of the connecting node
                if self.graph.node[node[0]]['cluster'] != self.graph.node[neighbor]['cluster']:
                    try:
                        self.g.remove_edge(node[0], neighbor)
                    except nx.exception.NetworkXError:
                        pass
                    self.removed_edges.append((node[0], neighbor))

    def _get_clusters(self):
        """Get final result of the k-clique percolation clustering.

        Returns
        -------
        clusters    : dict[list]
            Dictionary of list containing nodes identifier for each cluster.
        """
        clusters = {}
        cluster_id = 0
        for components in nx.connected_components(self.g):
            clusters[cluster_id] = components
            cluster_id += 1

        # refine cluster id
        ClusterUtility.set_cluster_id(self.graph, clusters)

        return clusters


class KCliquePercolationWeighted(KCliquePercolation):
    """This a class derived from KCliquePercolation for the case of weighted graph.
    """
    def __init__(self, graph, edges_weight, nodes_id, k, threshold):
        """This is the constructor for class KCliquePercolationWeighted.

        Parameters
        ----------
        graph           : graph
            A graph to be processed for its cluster.
        edges_weight    : list[tuple]
            List of tuple containing (node1, node2, cosine similarity between these two).
        nodes_id        : list
            List of all node identifier.
        k               : int
            Number of percolation or intersection between an individual clique.
        threshold       : float
            Threshold for the geometric mean.
        """
        print 'kclique_percolation_weighted: initialization ...'
        super(KCliquePercolationWeighted, self).__init__(graph, edges_weight, nodes_id, k)
        self.threshold = threshold

    def _find_kcliques(self):
        """This method will find weighted k-clique.

        The weight of k-clique is calculated based on the geometric mean of its weights.

        Returns
        -------
        weighted_kcliques   : list[frozenset]
            List of frozenset containing nodes identifier for each k-clique found.
        """
        print 'find_weighted_kclique ...'
        kcliques = super(KCliquePercolationWeighted, self)._find_kcliques()
        weighted_kcliques = ClusterUtility.get_weighted_cliques(self.graph, kcliques, self.threshold)

        return weighted_kcliques
