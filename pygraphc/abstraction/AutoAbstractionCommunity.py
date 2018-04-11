import networkx as nx
import os
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
        self.previous_clusters = {}

    def __get_community_detection(self):
        # create graph
        graph_model = CreateGraphModel(self.log_file)
        self.graph = graph_model.create_graph()
        self.graph_noattributes = graph_model.create_graph_noattributes()

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

    def __get_count_groups(self):
        abstraction_id = 0
        for cluster_id, nodes in self.clusters.iteritems():
            count_groups = {}
            for node_id in nodes:
                node_id = int(node_id)
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
        for abstraction_id, candidates in self.abstraction_candidates.iteritems():
            for count, candidate in candidates.iteritems():
                # transpose row to column
                candidate_transpose = list(zip(*candidate.values()))
                candidate_length = len(candidate.values())
                if candidate_length > 1:
                    # prevent initialization to refer to current group variable
                    self.abstractions[abstraction_id] = {'original_id': [],
                                                         'abstraction': candidate.values()[0]}

                    # get abstraction
                    abstraction_string = []
                    for index, message in enumerate(candidate_transpose):
                        message_length = len(set(message))
                        if message_length == 1:
                            abstraction_string.append(message[0])
                        else:
                            abstraction_string.append('*')
                    self.abstractions[abstraction_id]['abstraction'] = abstraction_string

                    for index, message in candidate.iteritems():
                        # set original line id
                        self.abstractions[abstraction_id]['original_id'].extend(self.graph.node[index]['member'])

                        # check for abstraction that only contains one word
                        # the abstraction is its original message in count group
                        if len(self.abstractions[abstraction_id]['abstraction']) == 1:
                            self.abstractions[abstraction_id]['abstraction'] = message

                elif candidate_length == 1:
                    node_id = candidate.keys()[0]
                    self.abstractions[abstraction_id] = {'original_id': self.graph.node[node_id]['member'],
                                                         'abstraction': candidate.values()[0]}
                abstraction_id += 1

    def __check_asterisk_only(self, abstraction_id, abstraction_list):
        # if abstraction only contains asterisks, each candidate becomes an abstraction
        if set(abstraction_list) == set('*'):
            print self.abstractions[abstraction_id]

    def __check_subabstraction(self):
        # check whether an abstraction is a substring of another abstraction
        pass

    def __print(self):
        for k, v in self.abstraction_candidates.iteritems():
            print self.abstractions[k]['abstraction']
            for x, y in v.iteritems():
                for p, q in y.iteritems():
                    print k, q
            print '-----------------------------------------'

        for k, v in self.clusters.iteritems():
            print k, v

    def get_abstraction(self):
        self.__get_community_detection()
        self.__get_count_groups()
        self.__get_abstraction_asterisk()
        self.__print()


aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/dmesg')
aa.get_abstraction()
