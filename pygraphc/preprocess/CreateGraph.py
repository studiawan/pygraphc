from itertools import combinations
import networkx as nx
from pygraphc.similarity.StringSimilarity import StringSimilarity


class CreateGraph(object):
    """A class for generating graph from preprocessed logs.
    """
    def __init__(self, events_unique, cosine_threshold=0):
        """Constructor for class CreateGraph.

        Parameters
        ----------
        events_unique       : list[list]
            List of unique events from preprocessed logs.
        cosine_threshold    : float
            Threshold of cosine similarity measure for edge weight.
        """
        self.events_unique = events_unique
        self.g = nx.MultiGraph()
        self.edges_dict = {}
        self.edges_weight = []
        self.cosine_threshold = cosine_threshold

    def do_create(self):
        """Main method to be executed to create a graph.
        """
        self.__create_nodes()
        self.__create_edges()

    def get_nodes_id(self):
        """Get node identifier.

        Returns
        -------
        nodes   : list[int]
            List of node identifier in incremental integer.
        """
        total_nodes = len(self.events_unique)
        nodes = [i for i in xrange(total_nodes)]
        return nodes

    def __create_nodes(self):
        """Create nodes in the graph from unique events.
        """
        self.g.add_nodes_from(self.events_unique)

    def __create_edges(self):
        """Create all edges in the graph based on cosine similarity measure.
        """
        edges_combinations = [eu[0] for eu in self.events_unique]
        edge_index = 0
        for ec in combinations(edges_combinations, 2):
            # get cosine similarity between two nodes
            tfidf1, tfidf2 = self.g.node[ec[0]]['tf-idf'], self.g.node[ec[1]]['tf-idf']
            length1, length2 = self.g.node[ec[0]]['length'], self.g.node[ec[1]]['length']
            cosine_similarity = StringSimilarity.get_cosine_similarity(tfidf1, tfidf2, length1, length2)

            # create edge if cosine similarity measure is bigger then threshold
            if cosine_similarity > self.cosine_threshold:
                self.g.add_edge(ec[0], ec[1], weight=cosine_similarity)
                self.edges_weight.append((ec[0], ec[1], cosine_similarity))
                self.edges_dict[(ec[0], ec[1])] = edge_index
                edge_index += 1
