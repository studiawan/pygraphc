import networkx as nx
from collections import deque
from itertools import chain, islice, combinations
from ClusterUtility import ClusterUtility


class KCliquePercolation(object):
    def __init__(self, graph, edges_weight, nodes_id, k):
        print 'kclique_percolation: initialization ...'
        self.graph = graph
        self.edges_weight = edges_weight
        self.nodes_id = nodes_id
        self.k = k
        self.g = None
        self.percolated_nodes = []
        self.removed_edges = []
        self.clique_percolation = []

    def get_percolation_nodes(self):
        return self.percolated_nodes

    def get_removed_edges(self):
        return self.removed_edges

    def get_clique_percolation(self):
        return self.clique_percolation

    def get_kclique_percolation(self):
        print 'get_kclique_percolation ...'
        self._build_temp_graph()
        kcliques = self._find_kcliques()
        self._get_percolation_graph(kcliques)
        self._remove_outcluster()
        clusters = self._get_clusters()

        return clusters

    def _find_kcliques(self):
        k_cliques = list(self._enumerate_all_cliques())
        kcliques = [frozenset(clique) for clique in k_cliques if len(clique) == self.k]

        return kcliques

    def _build_temp_graph(self):
        self.g = nx.Graph()
        self.g.add_nodes_from(self.nodes_id)
        self.g.add_weighted_edges_from(self.edges_weight)

    def _enumerate_all_cliques(self):
        # https://networkx.github.io/documentation/development/_modules/networkx/algorithms/clique.html#enumerate_all_cliques
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
        percolation_graph = nx.Graph()
        percolation_graph.add_nodes_from(kcliques)

        # Add an edge in the percolation graph for each pair of cliques that percolate
        for clique1, clique2 in combinations(kcliques, 2):
            percolation = clique1.intersection(clique2)
            self.percolated_nodes.append(percolation)
            if len(percolation) >= (self.k - 1):
                percolation_graph.add_edge(clique1, clique2)

        # Get all connected component in percolation graph
        self.clique_percolation = []
        for component in nx.connected_components(percolation_graph):
            self.clique_percolation.append(frozenset.union(*component))

        # set cluster id
        ClusterUtility.set_cluster_id(self.graph, self.clique_percolation)

    def _remove_outcluster(self):
        # remove edge outside cluster
        for node in self.g.nodes_iter(data=True):
            neighbors = self.g.neighbors(node[0])
            for neighbor in neighbors:
                if self.graph.node[node[0]]['cluster'] != self.graph.node[neighbor]['cluster']:
                    try:
                        self.g.remove_edge(node[0], neighbor)
                    except nx.exception.NetworkXError:
                        pass
                    self.removed_edges.append((node[0], neighbor))

    def _get_clusters(self):
        clusters = []
        for component in nx.connected_components(self.g):
            clusters.append(component)

        # refine cluster id
        ClusterUtility.set_cluster_id(self.graph, clusters)

        return clusters


class KCliquePercolationWeighted(KCliquePercolation):
    def __init__(self, graph, edges_weight, nodes_id, k, threshold):
        print 'kclique_percolation_weighted: initialization ...'
        super(KCliquePercolationWeighted, self).__init__(graph, edges_weight, nodes_id, k)
        self.threshold = threshold

    def _find_kcliques(self):
        print 'find_weighted_kclique ...'
        kcliques = super(KCliquePercolationWeighted, self)._find_kcliques()
        weighted_kcliques = ClusterUtility.get_weighted_cliques(self.graph, kcliques, self.threshold)

        return weighted_kcliques