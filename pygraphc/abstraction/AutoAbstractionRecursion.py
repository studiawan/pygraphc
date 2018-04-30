import networkx as nx
import os
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvain import Louvain


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.clusters = []

    def __prepare_graph(self, cluster=None):
        # create new temporary graph based on subgraph nodes
        if cluster:
            subgraph = [int(node) for node in cluster]
            self.graph_model.create_graph_subgraph(subgraph)
            graph_noattributes = self.graph_model.create_graph_noattributes(subgraph)

        # create graph
        else:
            self.graph_model = CreateGraphModel(self.log_file)
            self.graph = self.graph_model.create_graph()
            self.graph_noattributes = self.graph_model.create_graph_noattributes()
            self.graph_copy = self.graph.copy()
            graph_noattributes = self.graph_noattributes

        # write to gexf file
        filename = self.log_file.split('/')[-1]
        gexf_file = os.path.join('/', 'tmp', filename + '.gexf')
        nx.write_gexf(graph_noattributes, gexf_file)

        return gexf_file

    def __get_community(self, subgraph=None):
        # prepare graph or subgraph
        if subgraph:
            gexf_file = self.__prepare_graph(subgraph)
        else:
            gexf_file = self.__prepare_graph()

        # graph clustering based on Louvain community detection
        louvain = Louvain(gexf_file)
        clusters = louvain.get_cluster()

        # stop-recursion case: if there is no more partition
        if len(clusters.keys()) == 1:
            self.clusters.append(clusters.values()[0])
            print 'cluster with len=1', clusters.values()[0]

        # recursion case: graph clustering
        else:
            for cluster_id, cluster in clusters.iteritems():
                self.__get_community(cluster)

    def get_abstraction(self):
        self.__get_community()


# aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/messages')
# aa.get_abstraction()
