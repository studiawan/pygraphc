import networkx as nx
from random import choice
from itertools import combinations, product


class DaviesBouldinIndex(object):
    def __init__(self, graph, clusters):
        self.graph = graph
        self.clusters = clusters
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
        self.total_cluster = 0
        self.total_nodes = 0

        # get cluster properties: centroid per cluster, total nodes per cluster
        self.__get_all_cluster_properties()

    def __get_centroid(self, cluster=None):
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
        # get cluster centroid and cluster total nodes
        for cluster_id, nodes in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(nodes)
            self.cluster_total_nodes[cluster_id] = len(nodes)
        self.total_cluster = len(self.clusters.values())
        self.total_nodes = self.graph.number_of_nodes()

    def __get_distance(self, source, dest):
        # get distance from source to destination
        try:
            distance = nx.dijkstra_path_length(self.graph, source, dest)
        except nx.NetworkXNoPath:
            distance = 0.

        return distance

    def __get_dispersion(self):
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
        cluster_dissimilarity = {}
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            cluster_dissimilarity[(cluster_id1, cluster_id2)] = self.__get_distance(self.cluster_centroids[cluster_id1],
                                                                                    self.cluster_centroids[cluster_id2])
        return cluster_dissimilarity

    def __get_similarity(self):
        similarity = {}
        cluster_dispersions = self.__get_dispersion()
        cluster_dissimilarity = self.__get_dissimilarity()
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            similarity[cluster_id1, cluster_id2] = \
                cluster_dispersions[cluster_id1] + cluster_dispersions[cluster_id2] / \
                cluster_dissimilarity[(cluster_id1, cluster_id2)]

        return similarity

    def __get_r(self):
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
        r = self.__get_r()
        db_index = 1 / self.total_cluster * sum(r.values())

        return db_index
