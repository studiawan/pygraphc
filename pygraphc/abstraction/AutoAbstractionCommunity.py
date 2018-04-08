import networkx as nx
from orderedset import OrderedSet
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvan import Louvan


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.graph = None
        self.graph_noattributes = None
        self.clusters = {}
        self.abstraction_candidates = {}
        self.abstractions = {}

    def __get_community_detection(self):
        graph_model = CreateGraphModel(self.log_file)
        self.graph = graph_model.create_graph()
        self.graph_noattributes = graph_model.create_graph_noattributes()
        nx.write_gexf(self.graph_noattributes, '/tmp/graph.gexf')

        # graph clustering based on Louvan community detection
        louvan = Louvan()
        self.clusters = louvan.get_cluster()

    def __get_count_groups(self):
        abstraction_id = 0
        for cluster_id, nodes in self.clusters.iteritems():
            count_groups = {}
            for node_id in nodes:
                # we need OrderedSet to preserve order because a regular set does not preserve order
                node_id = int(node_id)
                message = self.graph.node[node_id]['preprocessed_event']
                words_split = OrderedSet(message.strip().split())
                words_count = len(words_split)

                # save count group per cluster
                if words_count not in count_groups.keys():
                    count_groups[words_count] = {}
                count_groups[words_count][node_id] = words_split

            for count, group in count_groups.iteritems():
                self.abstraction_candidates[abstraction_id] = {count: group}
                abstraction_id += 1

    def __get_abstraction_asterisk(self):
        # get abstraction with asterisk sign
        for abstraction_id, candidates in self.abstraction_candidates.iteritems():
            for count, candidate in candidates.iteritems():
                candidate_length = len(candidate.values())
                if candidate_length > 1:
                    # get abstraction
                    # prevent initialization to refer to current group variable. re-initialize with OrderedSet()
                    self.abstractions[abstraction_id] = {'original_id': [],
                                                         'abstraction': OrderedSet(candidate.values()[0])}
                    for index, message in candidate.iteritems():
                        self.abstractions[abstraction_id]['original_id'].extend(self.graph.node[index]['member'])
                        self.abstractions[abstraction_id]['abstraction'].intersection_update(message)

                    # check for abstraction that only contains one word,
                    # the abstraction is its original message in count group
                    if len(self.abstractions[abstraction_id]['abstraction']) == 1:
                        for index, message in candidate.iteritems():
                            self.abstractions[abstraction_id] = {'original_id': [self.graph.node[index]['member']],
                                                                 'abstraction': list(message)}
                            abstraction_id += 1
                    else:
                        # get index for abstraction
                        abstraction_index = set()
                        for word in self.abstractions[abstraction_id]['abstraction']:
                            abstraction_index.add(candidate.values()[0].index(word))

                        # get all index in original count_group and get asterisk index
                        all_index = set(range(len(candidate.values()[0])))
                        asterisk_index = all_index - abstraction_index
                        final_abstraction = list(self.abstractions[abstraction_id]['abstraction'])

                        # abstraction with asterisk symbol to represent the non-intersection words
                        for index in asterisk_index:
                            final_abstraction.insert(index, '*')
                        self.abstractions[abstraction_id]['abstraction'] = final_abstraction

                        abstraction_id += 1

                    # check if abstraction only contains asterisks
                    if set(self.abstractions[abstraction_id - 1]['abstraction']) == {'*'}:
                        abstraction_id -= 1
                        for index, message in candidate.iteritems():
                            self.abstractions[abstraction_id] = {'original_id': [self.graph.node[index]['member']],
                                                                 'abstraction': list(message)}
                            abstraction_id += 1

                elif candidate_length == 1:
                    node_id = candidate.keys()[0]
                    self.abstractions[abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                         'abstraction': list(candidate.values()[0])}

    def __check_subabstraction(self):
        # check whether an abstraction is a substring of another abstraction
        pass

    def get_abstraction(self):
        self.__get_community_detection()
        self.__get_count_groups()
        self.__get_abstraction_asterisk()


# aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/auth.log')
# aa.get_abstraction()
