import networkx as nx
import os
from operator import itemgetter
from itertools import combinations
from collections import Counter
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvain import Louvain


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.clusters = {}
        self.cluster_id = 0
        self.abstraction_candidates = {}
        self.candidate_id = 0
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
                abstraction_candidates[self.candidate_id] = {count: group}
                self.abstraction_candidates[self.candidate_id] = {count: group}
                self.candidate_id += 1

        return abstraction_candidates

    def __get_abstraction_asterisk(self, abstraction_candidates):
        # get abstraction with asterisk sign
        check_abstraction_id = []
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
                                                              'nodes': [],
                                                              'candidate_id': 0}
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
                                                                      'nodes': [node_id],
                                                                      'candidate_id': abs_id}
                            check_abstraction_id.append(self.abstraction_id)
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
                        self.abstractions[self.abstraction_id]['candidate_id'] = abs_id
                        check_abstraction_id.append(self.abstraction_id)
                        self.abstraction_id += 1

                # create abstraction
                elif candidate_length == 1:
                    node_id = candidate.keys()[0]
                    abstraction = candidate.values()[0]
                    self.abstractions[self.abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                              'abstraction': ' '.join(abstraction),
                                                              'length': len(abstraction),
                                                              'nodes': [node_id],
                                                              'candidate_id': abs_id}
                    check_abstraction_id.append(self.abstraction_id)
                    self.abstraction_id += 1

        return check_abstraction_id

    def __get_new_community(self, abstraction_id, cluster_id):
        # get nodes to run re-cluster
        clusters = {}
        nodes = self.abstractions[abstraction_id]['nodes']
        gexf_file = os.path.join('/', 'tmp', self.log_file.split('/')[-1] + str(abstraction_id) + '.gexf')

        # create new temporary graph based on subgraph nodes
        self.graph_model.create_graph_subgraph(nodes)

        # create graph with no attributes to be written to gexf file
        subgraph_noattributes = self.graph_model.create_graph_noattributes(nodes)
        nx.write_gexf(subgraph_noattributes, gexf_file)

        # graph clustering based on Louvain community detection
        louvain = Louvain(gexf_file)
        new_clusters = louvain.get_cluster()

        # save new found clusters
        for index, new_cluster in new_clusters.iteritems():
            nodes = [int(node) for node in new_cluster]
            clusters[cluster_id] = nodes
            cluster_id += 1

        return clusters, cluster_id

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

        # checked abstraction id
        check_abstraction_id = []
        for index1, index2_list in index_combination.iteritems():
            for index2 in index2_list:
                if count_sorted[index1][2] in count_sorted[index2][2]:
                    # get nodes to run re-cluster
                    abstraction_id_shorter_string = count_sorted[index1][3]
                    if abstraction_id_shorter_string not in check_abstraction_id:
                        cluster, cluster_id = self.__get_new_community(abstraction_id_shorter_string, cluster_id)
                        clusters.update(cluster)

                        # checked abstraction id
                        check_abstraction_id.append(abstraction_id_shorter_string)

                    abstraction_id_longer_string = count_sorted[index2][3]
                    if abstraction_id_longer_string not in check_abstraction_id:
                        cluster, cluster_id = self.__get_new_community(abstraction_id_longer_string, cluster_id)
                        clusters.update(cluster)

                        # checked abstraction id
                        check_abstraction_id.append(abstraction_id_longer_string)

                    break

        # additional abstraction candidates
        abstraction_candidates = self.__get_count_groups(clusters)
        additional_abstraction_id = self.__get_abstraction_asterisk(abstraction_candidates)
        check_abstraction_id.extend(additional_abstraction_id)

        return check_abstraction_id

    def __check_all_asterisk(self, checked_abstraction_id):

        for abstraction_id in checked_abstraction_id:
            # check for a particular node
            nodes = self.abstractions[abstraction_id]['nodes']
            node_id = nodes[0]

            # get intersection
            event_count_group = self.graph.node[node_id]['preprocessed_event_countgroup']
            event_graph_edge = self.graph.node[node_id]['preprocessed_events_graphedge'].split()
            event_intersection = list((Counter(event_count_group) & Counter(event_graph_edge)).elements())

            # get abstraction
            abstraction = self.abstractions[abstraction_id]['abstraction']
            abstraction_split = abstraction.split()

            # get asterisk and intersection indices
            asterisk_indices = [index for index, word in enumerate(abstraction_split) if word == '*']
            intersection_indices = []
            for word1 in event_intersection:
                for index, word2 in enumerate(event_count_group):
                    if word1 == word2:
                        intersection_indices.append(index)
            intersection_indices = sorted(set(intersection_indices))

            # asterisk indices are incremental
            if len(asterisk_indices) > 1:
                if asterisk_indices == range(asterisk_indices[0], asterisk_indices[-1] + 1) \
                        and asterisk_indices[-1] == (len(abstraction_split) - 1):

                    if set(asterisk_indices) <= set(intersection_indices) or \
                                    set(asterisk_indices) >= set(intersection_indices):

                        # each abstraction candidate become a new abstraction
                        candidate_id = self.abstractions[abstraction_id]['candidate_id']
                        candidates = self.abstraction_candidates[candidate_id]
                        for word_count, candidate in candidates.iteritems():
                            for node_id, message in candidate.iteritems():
                                self.abstractions[self.abstraction_id] = \
                                    {'original_id': self.graph.node[node_id]['member'],
                                     'abstraction': ' '.join(message),
                                     'length': len(message),
                                     'nodes': [node_id],
                                     'candidate_id': candidate_id}
                                self.abstraction_id += 1

                        # reset abstraction
                        self.abstractions[abstraction_id] = {'original_id': [], 'abstraction': [],
                                                             'length': 0, 'nodes': [], 'candidate_id': 0}

    @staticmethod
    def __remove_one_character(abstraction):
        line_split = abstraction.split()
        for index, word in enumerate(line_split):
            if len(word) == 1 and word != '*':
                line_split[index] = ''

        # remove more than one space
        line = ' '.join(line_split)
        line = ' '.join(line.split())

        return line

    def __get_final_abstractions(self):
        final_id = 0
        abstraction_only = []
        for abstraction_id, abstraction in self.abstractions.iteritems():
            # remove empty abstraction, remove duplicates
            if abstraction['abstraction']:
                # remove word with length only 1 character
                # abstraction['abstraction'] = self.__remove_one_character(abstraction['abstraction'])

                # final abstraction
                if abstraction['abstraction'] not in abstraction_only:
                    self.final_abstractions[final_id] = abstraction
                    abstraction_only.append(abstraction['abstraction'])
                    final_id += 1

    def get_abstraction(self):
        clusters = self.__get_community()
        abstraction_candidates = self.__get_count_groups(clusters)
        self.__get_abstraction_asterisk(abstraction_candidates)
        check_abstraction_id = self.__check_subabstraction()
        self.__check_all_asterisk(check_abstraction_id)
        self.__get_final_abstractions()

        return self.final_abstractions


# aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/messages')
# aa.get_abstraction()
