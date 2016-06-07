import networkx as nx
from itertools import combinations


class MaxCliquesPercolation:
    def __init__(self, g, k):
        self.g = g
        self.k = k

    def get_maxcliques_percolation(self):
        # Source: https://gist.github.com/conradlee/1341933
        percolation_graph = nx.Graph()
        cliques = list(frozenset(c) for c in nx.find_cliques(self.g) if len(c) >= self.k)
        percolation_graph.add_nodes_from(cliques)

        # Add an edge in the clique graph for each pair of cliques that percolate
        for c1, c2 in combinations(cliques, 2):
            if len(c1.intersection(c2)) >= (self.k - 1):
                percolation_graph.add_edge(c1, c2)

        percolation_result = []
        for component in nx.connected_components(percolation_graph):
            percolation_result.append(frozenset.union(*component))

        return cliques, percolation_result


class MaxCliquesPercolationWeighted(MaxCliquesPercolation):
    def __init__(self, g, k):
        MaxCliquesPercolation.__init__(self, g, k)
        self.percolation_dict = {}

    def get_maxcliques_percolation_weighted(self):
        cliques, percolations = self.get_maxcliques_percolation()
        self.__set_percolation_dict(percolations)
        for p1, p2 in combinations(percolations, 2):
            intersections = p1.intersection(p2)
            if intersections:
                for node in intersections:
                    node_neighbors = self.g.neighbors(node)
                    p1_neighbors, p2_neighbors = p1.intersection(node_neighbors), p2.intersection(node_neighbors)
                    p1_neighbors_weight = self.__get_neighbors_weight(node, p1_neighbors)
                    p2_neighbors_weight = self.__get_neighbors_weight(node, p2_neighbors)

                    self.percolation_dict[node] = self.percolation_dict[list(p1_neighbors)[0]] \
                        if p1_neighbors_weight > p2_neighbors_weight else self.percolation_dict[list(p2_neighbors)[0]]

        self.__set_graph_cluster()
        clusters = self.__get_clusters()
        return clusters

    def __set_percolation_dict(self, percolations):
        nodes = self.g.nodes()
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
            weight += self.g[node][n][0]['weight']

        return weight

    def __set_graph_cluster(self):
        for node in self.g.nodes_iter(data=True):            
            self.g.node[node[0]]['cluster'] = self.percolation_dict[node[0]]
        return self.g
    
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