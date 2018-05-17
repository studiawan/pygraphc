from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.similarity.CosineSimilarity import ParallelCosineSimilarity
from pygraphc.pruning.TrianglePruning import TrianglePruning
import networkx as nx


class CreateGraphModel(object):
    def __init__(self, log_file='', count_groups=None, pruning=False):
        self.log_file = log_file
        self.log_length = 0
        self.unique_events = []
        self.unique_events_length = 0
        self.event_attributes = {}
        self.preprocessed_logs = {}
        self.preprocessed_logs_groundtruth = {}
        self.distances = []
        self.graph = nx.MultiGraph()
        self.count_groups = count_groups
        self.edges_weight = self.distances
        self.pruning = pruning
        self.logs = []
        self.events_withduplicates = []
        self.events_withduplicates_length = 0
        self.graph_noattributes = nx.Graph()
        self.subgraph = nx.MultiGraph()
        self.subgraph_noattributes = nx.Graph()
        self.pp = None

    def __get_nodes(self):
        # preprocess logs and get unique events as nodes in a graph
        self.pp = ParallelPreprocess(self.log_file)
        self.unique_events = self.pp.get_unique_events()
        self.unique_events_length = self.pp.unique_events_length
        self.event_attributes = self.pp.event_attributes
        self.preprocessed_logs = self.pp.preprocessed_logs
        self.log_length = self.pp.log_length
        self.logs = self.pp.logs
        self.preprocessed_logs_groundtruth = self.pp.preprocessed_logs_groundtruth

    def __get_distances(self):
        # get cosine distance as edges with weight
        pcs = ParallelCosineSimilarity(self.event_attributes, self.unique_events_length)
        self.distances = pcs.get_parallel_cosine_similarity()

    def create_graph(self):
        # create graph with previously created nodes and edges
        self.__get_nodes()
        self.__get_distances()
        self.graph.add_nodes_from(self.unique_events)
        self.graph.add_weighted_edges_from(self.distances)

        if self.pruning:
            tp = TrianglePruning(self.graph)
            tp.get_triangle()
            self.graph = tp.graph

        return self.graph

    def __get_nodes_nopreprocess(self):
        # create nodes without log preprocessing
        pp = ParallelPreprocess('', True, self.count_groups)
        self.unique_events = pp.get_unique_events_nopreprocess()
        self.unique_events_length = pp.unique_events_length
        self.event_attributes = pp.event_attributes

    def __get_distances_nopreprocess(self):
        # create distances as edge weight
        pcs = ParallelCosineSimilarity(self.event_attributes, self.unique_events_length)
        self.distances = pcs.get_parallel_cosine_similarity()

    def create_graph_nopreprocess(self):
        # create graph without preprocessing logs
        self.__get_nodes_nopreprocess()
        self.__get_distances_nopreprocess()
        self.graph.add_nodes_from(self.unique_events)
        self.graph.add_weighted_edges_from(self.distances)

        return self.graph

    def __get_nodes_withduplicates(self):
        # create nodes without creating unique event. every log line is now a node
        pp = ParallelPreprocess('', True, self.count_groups)
        self.events_withduplicates = pp.get_events_withduplicates()
        self.events_withduplicates_length = pp.events_withduplicates_length
        self.event_attributes = pp.event_attributes

    def __get_distances_withduplicates(self):
        # create distances as edge weight
        pcs = ParallelCosineSimilarity(self.event_attributes, self.events_withduplicates_length)
        self.distances = pcs.get_parallel_cosine_similarity()

    def create_graph_withduplicates(self):
        # create graph without preprocessing logs
        self.__get_nodes_withduplicates()
        self.__get_distances_withduplicates()
        self.graph.add_nodes_from(self.unique_events)
        self.graph.add_weighted_edges_from(self.distances)

        return self.graph

    def create_graph_noattributes(self, nodes=None):
        if nodes:
            self.subgraph_noattributes = nx.Graph()
            self.subgraph_noattributes.add_nodes_from(nodes)
            self.subgraph_noattributes.add_weighted_edges_from(self.distances_subgraph)
            return self.subgraph_noattributes

        else:
            nodes = range(self.unique_events_length)
            self.graph_noattributes.add_nodes_from(nodes)
            self.graph_noattributes.add_weighted_edges_from(self.distances)
            return self.graph_noattributes

    def __get_nodes_subgraph(self, nodes):
        self.unique_events_subgraph = []
        for unique_event in self.unique_events:
            index = unique_event[0]
            attributes = unique_event[1]
            if index in nodes:
                self.unique_events_subgraph.append((index, attributes))

        self.unique_events_length_subgraph = len(nodes)
        self.event_attributes_subgraph = {}
        for index, attributes in self.event_attributes.iteritems():
            if index in nodes:
                self.event_attributes_subgraph[index] = attributes

        # remove same word, same column
        self.unique_events_subgraph, self.event_attributes_subgraph, self.graph = \
            self.pp.refine_preprocessed_event_graphedge(self.unique_events_subgraph,
                                                        self.event_attributes_subgraph,
                                                        self.graph)

    def __get_distances_subgraph(self, nodes):
        pcs = ParallelCosineSimilarity(self.event_attributes_subgraph, self.unique_events_length_subgraph, nodes)
        self.distances_subgraph = pcs.get_parallel_cosine_similarity()

    def create_graph_subgraph(self, nodes):
        self.subgraph = nx.Graph()
        self.__get_nodes_subgraph(nodes)
        self.__get_distances_subgraph(nodes)
        self.subgraph.add_nodes_from(self.unique_events_subgraph)
        self.subgraph.add_weighted_edges_from(self.distances_subgraph)

        return self.subgraph
