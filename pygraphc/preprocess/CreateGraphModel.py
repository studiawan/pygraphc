from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.similarity.JaroWinkler import JaroWinkler
import networkx as nx
from time import time


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
        jw = JaroWinkler(self.event_attributes, self.unique_events_length)
        self.distances = jw.get_jarowinkler()

    def create_graph(self):
        self.__get_nodes()
        self.__get_distances()
        self.graph.add_nodes_from(self.unique_events)
        self.graph.add_weighted_edges_from(self.distances)

        return self.graph

# open file
start = time()
logfile = '/home/hudan/Git/labeled-authlog/dataset/SecRepo/auth-perday/dec-1.log'

# preprocess
cgm = CreateGraphModel(logfile)
graph = cgm.create_graph()
nx.write_dot(graph, 'test.dot')

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
