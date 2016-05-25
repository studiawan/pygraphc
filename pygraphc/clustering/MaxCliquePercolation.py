import networkx as nx
from itertools import combinations


class MaxCliquePercolation:
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


class MaxCliquePercolationWeighted(MaxCliquePercolation):
    def __init__(self, g, k):
        MaxCliquePercolation.__init__(self, g, k)

    def get_percolation_dict(self, percolations):
        nodes = self.g.nodes()
        percolation_dict = {}
        for index, percolation in enumerate(percolations):
            for p in percolation:
                percolation_dict[p] = index

        diff = set(nodes).difference(percolations[0])
        if diff:
            other_cluster = len(percolations)
            for i in diff:
                percolation_dict[i] = other_cluster
                other_cluster += 1

        return percolation_dict

    def get_neighbors_weight(self, node, neighbors):
        weight = 0
        for n in neighbors:
            weight += self.g[node][n][0]['weight']

        return weight

    def get_cluster_member(self, percolation_dict):
        percolation_new = {}
        for node, cluster in percolation_dict.iteritems():
            percolation_new.setdefault(cluster, []).append(node)

        percolation_list = percolation_new.values()
        return percolation_list				

    def get_non_overlap(self):
        cliques, percolation = self.get_maxcliques_percolation()
        percolation_dict = self.get_percolation_dict(percolation)
        for p1, p2 in combinations(percolation, 2):
            intersections = p1.intersection(p2)
            if intersections:
                for node in intersections:
                    node_neighbors = self.g.neighbors(node)
                    p1_neighbors, p2_neighbors = p1.intersection(node_neighbors), p2.intersection(node_neighbors)
                    p1_neighbors_weight = self.get_neighbors_weight(node, p1_neighbors)
                    p2_neighbors_weight = self.get_neighbors_weight(node, p2_neighbors)

                    percolation_dict[node] = percolation_dict[list(p1_neighbors)[0]] if p1_neighbors_weight > p2_neighbors_weight else percolation_dict[list(p2_neighbors)[0]]

        percolation_list = self.get_cluster_member(percolation_dict)
        return percolation_list, percolation_dict

    def get_graph_cluster(self, percolation_dict):
        for node in self.g.nodes_iter(data=True):
            self.g[node[0]]['cluster'] = percolation_dict[node[0]]
        return self.g