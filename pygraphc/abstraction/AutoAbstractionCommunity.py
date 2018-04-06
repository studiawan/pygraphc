from orderedset import OrderedSet
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.Louvan import Louvan


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.graph = None
        self.clusters = {}
        self.abstraction_candidates = {}

    def __get_count_groups(self):
        abstraction_id = 0
        for cluster_id, nodes in self.clusters.iteritems():
            count_groups = {}
            for node_id in nodes:
                # we need OrderedSet to preserve order because a regular set does not preserve order
                message = self.graph.node[node_id]['preprocessed_event']
                words_split = OrderedSet(message.strip().split())
                words_count = len(words_split)

                # save count group per cluster
                if words_count not in count_groups.keys():
                    count_groups[words_count] = {}
                count_groups[words_count][node_id] = words_split

            self.abstraction_candidates[abstraction_id].update(count_groups)
            abstraction_id += 1

    def __get_community_detection(self):
        graph_model = CreateGraphModel(self.log_file)
        self.graph = graph_model.create_graph()

        # graph clustering based on Louvan community detection
        self.clusters = Louvan(self.graph)

    def get_abstraction(self):
        self.__get_community_detection()
        self.__get_count_groups()


# aa = AutoAbstraction('/home/hudan/Git/datasets/casper-rw/logs/auth.log')
# aa.get_abstraction()
