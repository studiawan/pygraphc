import networkx as nx
import community


class Louvan(object):
    def __init__(self):
        self.graph = None
        self.partition = {}
        self.clusters = {}

    def __get_community(self):
        self.graph = nx.read_gexf('/tmp/graph.gexf')
        self.partition = community.best_partition(self.graph)

    def get_cluster(self):
        self.__get_community()
        for node_id, partition_id in self.partition.iteritems():
            if partition_id not in self.clusters.keys():
                self.clusters[partition_id] = []
            self.clusters[partition_id].append(node_id)

        return self.clusters
