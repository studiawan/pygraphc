import networkx as nx
from random import choice


class CalinskiHarabaszIndex(object):
    def __init__(self, graph, clusters, total_nodes):
        self.graph = graph
        self.clusters = clusters
        self.total_nodes = total_nodes
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}

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

    def __get_distance(self, source, dest):
        # get distance from source to destination
        try:
            distance = nx.dijkstra_path_length(self.graph, source, dest)
        except nx.NetworkXNoPath:
            distance = 0.

        return distance

    def __get_trace_b(self):
        # get trace B
        traces_b = []
        graph_centroid = self.__get_centroid()
        for cluster_id, nodes in self.clusters.iteritems():
            trace_b = self.cluster_total_nodes[cluster_id] * \
                      (self.__get_distance(self.cluster_centroids[cluster_id], graph_centroid) ** 2)
            traces_b.append(trace_b)

        total_trace_b = sum(traces_b)
        return total_trace_b

    def __get_trace_w(self):
        # get trace W
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
        # get Calinski-Harabasz index
        total_cluster = len(self.clusters.values())
        ch_index = (self.__get_trace_b() / (total_cluster - 1)) / \
                   (self.__get_trace_w() / (self.total_nodes - total_cluster))

        return ch_index
