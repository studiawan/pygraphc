from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.similarity.CosineSimilarity import ParallelCosineSimilarity
from pygraphc.pruning.TrianglePruning import TrianglePruning
import networkx as nx


class CreateGraphModel(object):
    def __init__(self, log_file, count_groups=None, pruning=False):
        self.log_file = log_file
        self.log_length = 0
        self.unique_events = []
        self.unique_events_length = 0
        self.preprocessed_logs = {}
        self.distances = []
        self.graph = nx.MultiGraph()
        self.count_groups = count_groups
        self.edges_weight = self.distances
        self.pruning = pruning
        self.logs = []
        self.events_withduplicates = []
        self.events_withduplicates_length = 0
        self.graph_noattributes = nx.MultiGraph()

    def __get_nodes(self):
        # preprocess logs and get unique events as nodes in a graph
        pp = ParallelPreprocess(self.log_file)
        self.unique_events = pp.get_unique_events()
        self.unique_events_length = pp.unique_events_length
        self.event_attributes = pp.event_attributes
        self.preprocessed_logs = pp.preprocessed_logs
        self.log_length = pp.log_length
        self.logs = pp.logs

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

    def create_graph_noattributes(self):
        self.graph_noattributes.add_weighted_edges_from(self.distances)

        return self.graph_noattributes
