import networkx as nx
import os
from operator import itemgetter
from itertools import combinations
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvan import Louvan
from pygraphc.clustering.ClusterUtility import ClusterUtility


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.graph = None
        self.graph_copy = None
        self.graph_noattributes = None
        self.clusters = {}
        self.abstraction_candidates = {}
        self.abstractions = {}
        self.final_abstractions = {}

    def __get_community_detection(self):
        # create graph
        graph_model = CreateGraphModel(self.log_file)
        self.graph = graph_model.create_graph()
        self.graph_noattributes = graph_model.create_graph_noattributes()
        self.graph_copy = self.graph.copy()

        # start of phase 1
        # write to file
        gexf_file = os.path.join('/', 'tmp', self.log_file.split('/')[-1] + '.gexf')
        nx.write_gexf(self.graph_noattributes, gexf_file)

        # graph clustering based on Louvan community detection
        louvan = Louvan(gexf_file)
        temporary_clusters = louvan.get_cluster()

        # start of phase 2
        cluster_id = 0
        for temporary_index, temporary_cluster in temporary_clusters.iteritems():
            if len(temporary_cluster) == 1:
                self.clusters[cluster_id] = temporary_cluster
                cluster_id += 1
            else:
                # write to file
                gexf_file = os.path.join('/', 'tmp', self.log_file.split('/')[-1] + '.gexf')
                temporary_cluster = [int(node) for node in temporary_cluster]
                nx.write_gexf(self.graph_noattributes.subgraph(temporary_cluster), gexf_file)

                # graph clustering based on Louvan community detection
                louvan = Louvan(gexf_file)
                temporary_clusters2 = louvan.get_cluster()

                if len(temporary_clusters2.keys()) == 1:
                    self.clusters[cluster_id] = temporary_clusters2.values()[0]
                    cluster_id += 1
                else:
                    # start of phase 3
                    for temporary_index2, temporary_cluster2 in temporary_clusters2.iteritems():
                        # write to file
                        gexf_file = os.path.join('/', 'tmp', self.log_file.split('/')[-1] + '.gexf')
                        temporary_cluster2 = [int(node) for node in temporary_cluster2]
                        nx.write_gexf(self.graph_noattributes.subgraph(temporary_cluster2), gexf_file)

                        # graph clustering based on Louvan community detection
                        louvan = Louvan(gexf_file)
                        temporary_clusters3 = louvan.get_cluster()

                        if len(temporary_clusters3.keys()) == 1:
                            self.clusters[cluster_id] = temporary_clusters3.values()[0]
                            cluster_id += 1
                        else:
                            for temporary_index3, temporary_cluster3 in temporary_clusters3.iteritems():
                                self.clusters[cluster_id] = temporary_cluster3
                                cluster_id += 1

    def __check_all_node_id(self):
        check_node_id = {}
        for cluster_id, nodes in self.clusters.iteritems():
            for node in nodes:
                node = int(node)
                check_node_id[node] = cluster_id

        for key in sorted(check_node_id.iterkeys()):
            print "%s: %s" % (key, check_node_id[key])

    def __check_abstractions(self):
        for abstraction_id, abstraction in self.abstraction_candidates.iteritems():
            print abstraction_id, abstraction

    def __set_cluster_attribute(self):
        # set cluster id in cluster node attribute
        for cluster_id, clusters in self.clusters.iteritems():
            for node in clusters:
                self.graph_copy.node[int(node)]['cluster'] = cluster_id

    def __remove_outcluster(self):
        """Remove edges that connect to other clusters.

        This method will first find any edges in the cluster member. If edges connecting to a node does not belong to
        the current cluster, then it will be removed.
        """
        # remove edge outside cluster
        for node in self.graph_copy.nodes_iter(data=True):
            neighbors = self.graph_copy.neighbors(node[0])
            for neighbor in neighbors:
                # if cluster id of current node is not the same of the connecting node
                if self.graph_copy.node[node[0]]['cluster'] != self.graph_copy.node[neighbor]['cluster']:
                    try:
                        self.graph_copy.remove_edge(node[0], neighbor)
                    except nx.exception.NetworkXError:
                        pass

    def __get_clusters(self):
        """Get final result of the clustering.

        Returns
        -------
        clusters    : dict[list]
            Dictionary of list containing nodes identifier for each cluster.
        """
        clusters = {}
        cluster_id = 0
        for components in nx.connected_components(self.graph_copy):
            clusters[cluster_id] = components
            cluster_id += 1

        # refine cluster id
        ClusterUtility.set_cluster_id(self.graph_copy, clusters)
        self.clusters = clusters

    def __get_count_groups(self):
        abstraction_id = 0
        for cluster_id, nodes in self.clusters.iteritems():
            count_groups = {}
            for node_id in nodes:
                message = self.graph.node[node_id]['preprocessed_event'].split()
                words_count = len(message)

                # save count group per cluster
                if words_count not in count_groups.keys():
                    count_groups[words_count] = {}
                count_groups[words_count][node_id] = message

            for count, group in count_groups.iteritems():
                self.abstraction_candidates[abstraction_id] = {count: group}
                abstraction_id += 1

    def __get_abstraction_asterisk(self):
        # get abstraction with asterisk sign
        abstraction_id = 0
        for abs_id, candidates in self.abstraction_candidates.iteritems():
            for word_count, candidate in candidates.iteritems():
                # transpose row to column
                candidate_transpose = list(zip(*candidate.values()))
                candidate_length = len(candidate.values())
                if candidate_length > 1:
                    # prevent initialization to refer to current group variable
                    self.abstractions[abstraction_id] = {'original_id': [],
                                                         'abstraction': [],
                                                         'length': 0}
                    # get abstraction
                    abstraction_list = []
                    for index, message in enumerate(candidate_transpose):
                        message_length = len(set(message))
                        if message_length == 1:
                            abstraction_list.append(message[0])
                        else:
                            abstraction_list.append('*')

                    # if abstraction only contains asterisks, each candidate becomes an abstraction
                    if set(abstraction_list) == set('*'):
                        for node_id, message in candidate.iteritems():
                            self.abstractions[abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                                 'abstraction': ' '.join(message),
                                                                 'length': len(message)}
                            abstraction_id += 1

                    # set abstraction and original line id
                    else:
                        for node_id, message in candidate.iteritems():
                            self.abstractions[abstraction_id]['original_id'].extend(self.graph.node[node_id]['member'])
                        self.abstractions[abstraction_id]['abstraction'] = ' '.join(abstraction_list)
                        self.abstractions[abstraction_id]['length'] = len(abstraction_list)
                        abstraction_id += 1

                elif candidate_length == 1:
                    node_id = candidate.keys()[0]
                    abstraction = candidate.values()[0]
                    self.abstractions[abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                         'abstraction': ' '.join(abstraction),
                                                         'length': len(abstraction)}
                    abstraction_id += 1

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

        # check for subabtraction
        for index1, index2_list in index_combination.iteritems():
            for index2 in index2_list:
                if count_sorted[index1][2] in count_sorted[index2][2]:
                    # empty the member of shorter abstraction
                    shorter_member = self.abstractions[count_sorted[index1][3]]['original_id']
                    self.abstractions[count_sorted[index1][3]] = {'original_id': [],
                                                                  'abstraction': '',
                                                                  'length': 0}
                    # merge to longer abstraction then break
                    self.abstractions[count_sorted[index2][3]]['original_id'].extend(shorter_member)
                    break

        # final abstraction, left the empty abstraction behind
        final_id = 0
        for abstraction_id, abstraction in self.abstractions.iteritems():
            if abstraction['length'] > 0:
                self.final_abstractions[final_id] = abstraction
                final_id += 1

    def get_abstraction(self):
        self.__get_community_detection()
        self.__set_cluster_attribute()
        self.__remove_outcluster()
        self.__get_clusters()
        self.__get_count_groups()
        self.__get_abstraction_asterisk()
        self.__check_subabstraction()

        return self.final_abstractions
