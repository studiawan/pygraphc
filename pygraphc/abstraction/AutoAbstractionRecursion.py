import networkx as nx
import os
from operator import itemgetter
from itertools import combinations
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvain import Louvain


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.clusters = {}
        self.cluster_id = 0
        self.abstractions = {}
        self.abstraction_id = 0
        self.final_abstractions = {}

    def __prepare_graph(self, cluster=None):
        # create new temporary graph based on subgraph nodes
        if cluster:
            subgraph = [int(node) for node in cluster]
            graph_noattributes = self.graph_noattributes.subgraph(subgraph)

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
            nodes = [int(node) for node in clusters.values()[0]]
            self.clusters[self.cluster_id] = nodes
            self.cluster_id += 1

        # recursion case: graph clustering
        else:
            for cluster_id, cluster in clusters.iteritems():
                self.__get_community(cluster)

        return self.clusters

    def __get_count_groups(self, clusters):
        abstraction_id = 0
        abstraction_candidates = {}
        for cluster_id, nodes in clusters.iteritems():
            count_groups = {}
            for node_id in nodes:
                message = self.graph.node[node_id]['preprocessed_event_countgroup']
                words_count = len(message)

                # save count group per cluster
                if words_count not in count_groups.keys():
                    count_groups[words_count] = {}
                count_groups[words_count][node_id] = message

            for count, group in count_groups.iteritems():
                abstraction_candidates[abstraction_id] = {count: group}
                abstraction_id += 1

        return abstraction_candidates

    def __get_abstraction_asterisk(self, abstraction_candidates):
        # get abstraction with asterisk sign
        for abs_id, candidates in abstraction_candidates.iteritems():
            for word_count, candidate in candidates.iteritems():
                # transpose row to column
                candidate_transpose = list(zip(*candidate.values()))
                candidate_length = len(candidate.values())

                if candidate_length > 1:
                    # prevent initialization to refer to current group variable
                    self.abstractions[self.abstraction_id] = {'original_id': [],
                                                              'abstraction': [],
                                                              'length': 0,
                                                              'nodes': []}
                    # get abstraction
                    abstraction_list = []
                    for index, message in enumerate(candidate_transpose):
                        message_length = len(set(message))
                        if message_length == 1:
                            abstraction_list.append(message[0])
                        elif message_length > 1:
                            abstraction_list.append('*')

                    # if abstraction only contains asterisks, each candidate becomes an abstraction
                    if set(abstraction_list) == set('*'):
                        for node_id, message in candidate.iteritems():
                            self.abstractions[self.abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                                      'abstraction': ' '.join(message),
                                                                      'length': len(message),
                                                                      'nodes': [node_id]}
                            self.abstraction_id += 1

                    # set abstraction and original line id
                    else:
                        member_nodes = []
                        for node_id, message in candidate.iteritems():
                            member = self.graph.node[node_id]['member']
                            self.abstractions[self.abstraction_id]['original_id'].extend(member)
                            member_nodes.append(node_id)

                        self.abstractions[self.abstraction_id]['nodes'] = member_nodes
                        self.abstractions[self.abstraction_id]['abstraction'] = ' '.join(abstraction_list)
                        self.abstractions[self.abstraction_id]['length'] = len(abstraction_list)
                        self.abstraction_id += 1

                # create abstraction
                # based on
                # original log id
                # please check again
                elif candidate_length == 1:
                    node_id = candidate.keys()[0]
                    abstraction = candidate.values()[0]
                    self.abstractions[self.abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                              'abstraction': ' '.join(abstraction),
                                                              'length': len(abstraction),
                                                              'nodes': [node_id]}
                    self.abstraction_id += 1

    def __check_subabstraction(self):
        # check whether an abstraction is a substring of another abstraction
        # convert abstraction to list of tuple for sorting.
        # tuple: (abstraction_length, original_id, abstraction_string, abstraction_id)
        count_abstraction = []
        for abstraction_id, abstraction in self.abstractions.iteritems():
            count_abstraction.append((abstraction['length'], abstraction['original_id'],
                                      abstraction['abstraction'], abstraction_id))

        # sort abstraction based on word count
        count_sorted = sorted(count_abstraction, key=itemgetter(0))
        count_sorted_length = len(count_sorted)

        # save combinations to dictionary
        index_combination = {}
        for index1, index2 in combinations(range(count_sorted_length), 2):
            if index1 not in index_combination.keys():
                index_combination[index1] = []
            index_combination[index1].append(index2)

        # check for subabstraction
        cluster_id = 0
        clusters = {}
        for index1, index2_list in index_combination.iteritems():
            for index2 in index2_list:
                if count_sorted[index1][2] in count_sorted[index2][2]:
                    # get nodes to run re-cluster
                    abstraction_id_shorter_string = count_sorted[index1][3]
                    nodes = self.abstractions[abstraction_id_shorter_string]['nodes']
                    gexf_file = os.path.join('/', 'tmp', self.log_file.split('/')[-1] +
                                             str(abstraction_id_shorter_string) + '.gexf')

                    # create new temporary graph based on subgraph nodes
                    self.graph_model.create_graph_subgraph(nodes)

                    # create graph with no attributes to be written to gexf file
                    subgraph_noattributes = self.graph_model.create_graph_noattributes(nodes)
                    nx.write_gexf(subgraph_noattributes, gexf_file)

                    # graph clustering based on Louvain community detection
                    louvan = Louvain(gexf_file)
                    new_clusters = louvan.get_cluster()

                    # save new found clusters
                    for index, new_cluster in new_clusters.iteritems():
                        nodes = [int(node) for node in new_cluster]
                        clusters[cluster_id] = nodes
                        cluster_id += 1

                    # reset abstraction
                    self.abstractions[abstraction_id_shorter_string] = {'original_id': [], 'abstraction': [],
                                                                        'length': 0, 'nodes': []}
                    break

        # additional abstraction candidates
        abstraction_candidates = self.__get_count_groups(clusters)
        self.__get_abstraction_asterisk(abstraction_candidates)

        # final abstraction, left the empty abstraction behind
        final_id = 0
        for abstraction_id, abstraction in self.abstractions.iteritems():
            if abstraction['length'] > 0:
                self.final_abstractions[final_id] = abstraction
                final_id += 1

    def get_abstraction(self):
        clusters = self.__get_community()
        abstraction_candidates = self.__get_count_groups(clusters)
        self.__get_abstraction_asterisk(abstraction_candidates)
        # self.__check_subabstraction()


# aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/messages')
# aa.get_abstraction()
