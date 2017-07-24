from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.similarity.CosineSimilarity import ParallelCosineSimilarity
from pygraphc.pruning.TrianglePruning import TrianglePruning
import networkx as nx


class CreateGraphModel(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.unique_events = []
        self.unique_events_length = 0
        self.distances = []
        self.graph = nx.MultiGraph()

    def __get_nodes(self):
        pp = ParallelPreprocess(self.log_file)
        self.unique_events = pp.get_unique_events()
        self.unique_events_length = pp.unique_events_length
        self.event_attributes = pp.event_attributes

    def __get_distances(self):
        pcs = ParallelCosineSimilarity(self.event_attributes, self.unique_events_length)
        self.distances = pcs.get_parallel_cosine_similarity()

    def create_graph(self):
        self.__get_nodes()
        self.__get_distances()
        self.graph.add_nodes_from(self.unique_events)
        self.graph.add_weighted_edges_from(self.distances)

        tp = TrianglePruning(self.graph)
        tp.get_triangle()
        self.graph = tp.graph

        return self.graph
