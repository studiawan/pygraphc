import community
import networkx as nx


class GraphCut(object):
    def __init__(self, graph):
        self.partition_config = {}
        self.partition_id = 0
        self.graph = graph
        self.clusters = {}
        self.cluster_id = 0

    def __set_partition_config(self, partitions):
        for partition in partitions:
            for node_id in partition:
                self.partition_config[node_id] = self.partition_id
            self.partition_id += 1

    def __reset_partition_config(self):
        self.partition_id = 0
        map_id = {}
        for node_id, partition_id in self.partition_config.iteritems():
            if partition_id not in map_id.keys():
                map_id[partition_id] = self.partition_id
                self.partition_config[node_id] = self.partition_id
                self.partition_id += 1
            else:
                self.partition_config[node_id] = map_id[partition_id]

    def __graph_cut(self, graph, previous_modularity=None):
        # get graph cut
        cut_value, partitions = nx.stoer_wagner(graph)

        # run partition config and reset
        self.__set_partition_config(partitions)
        self.__reset_partition_config()

        # get modularity
        # note that to calculate modularity, we need configuration of
        # all partitions in a graph, not only subgraph
        current_modularity = community.modularity(self.partition_config, graph)
        # print previous_modularity, current_modularity

        # graph cut recursion
        if previous_modularity == current_modularity:
            for partition in partitions:
                self.clusters[self.cluster_id] = partition
                self.cluster_id += 1

        else:
            for partition in partitions:
                if len(partition) <= 3:
                    self.clusters[self.cluster_id] = partition
                    self.cluster_id += 1

                else:
                    self.__graph_cut(graph.subgraph(partition), current_modularity)

    def get_graph_cut(self):
        self.__graph_cut(self.graph)
        return self.clusters
