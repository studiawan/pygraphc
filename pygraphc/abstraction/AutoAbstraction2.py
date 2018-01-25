from orderedset import OrderedSet
from operator import itemgetter
from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.GraphEntropy import GraphEntropy


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.unique_events = []
        self.count_groups = {}
        self.count_groups_refine = {}
        self.abstractions = {}

    def __get_unique_events(self):
        pp = ParallelPreprocess(self.log_file)
        self.unique_events = pp.get_unique_events()

    def __get_count_groups(self):
        self.__get_unique_events()
        for event_id, attributes in self.unique_events:
            message = attributes['preprocessed_event']

            # we need OrderedSet to preserve order because a regular set does not preserve order
            words_split = OrderedSet(message.strip().split())
            words_count = len(words_split)

            # group based on word count
            group_keys = self.count_groups.keys()
            if words_count not in group_keys:
                self.count_groups[words_count] = {}
            self.count_groups[words_count][event_id] = words_split

    def __refine_count_groups(self):
        self.__get_count_groups()
        refine_id = 0
        for words_count, count_group in self.count_groups.iteritems():
            group_length = len(count_group)

            # refine with graph clustering
            if group_length > 1:
                # create nodes, edges, and graph
                preprocess = CreateGraphModel('', count_group)
                graph = preprocess.create_graph_nopreprocess()

                # graph clustering based on entropy
                ge = GraphEntropy(graph)
                clusters = ge.get_graph_entropy()

                # get new groups, if exists
                for cluster_id, nodes in clusters.iteritems():
                    self.count_groups_refine[refine_id] = {}
                    for node in nodes:
                        # convert node id in graph clusters to original id of count group
                        original_id = graph.node[node]['original_id']
                        self.count_groups_refine[refine_id][original_id] = count_group[original_id]
                    refine_id += 1

            elif group_length == 1:
                self.count_groups_refine[refine_id] = count_group
                refine_id += 1

    def get_abstraction(self):
        # group messages which has the same word count
        self.__refine_count_groups()

        # get common words with intersection as abstraction
        abstraction_id = 0
        for words_count, group in self.count_groups_refine.iteritems():
            group_length = len(group.values())
            if group_length > 1:
                # get abstraction
                # prevent initialization to refer to current group variable. re-initialize with OrderedSet()
                self.abstractions[abstraction_id] = {'original_id': [],
                                                     'abstraction': OrderedSet(group.values()[0])}
                for index, message in group.iteritems():
                    self.abstractions[abstraction_id]['original_id'].append(index)
                    self.abstractions[abstraction_id]['abstraction'].intersection_update(message)

                # check for abstraction that only contains one word,
                # the abstraction is its original message in count group
                if len(self.abstractions[abstraction_id]['abstraction']) == 1:
                    for index, message in group.iteritems():
                        self.abstractions[abstraction_id] = {'original_id': [index],
                                                             'abstraction': list(message)}
                        abstraction_id += 1
                else:
                    # get index for abstraction
                    abstraction_index = set()
                    for word in self.abstractions[abstraction_id]['abstraction']:
                        abstraction_index.add(group.values()[0].index(word))

                    # get all index in original count_group and get asterisk index
                    all_index = set(range(len(group.values()[0])))
                    asterisk_index = all_index - abstraction_index
                    final_abstraction = list(self.abstractions[abstraction_id]['abstraction'])

                    # abstraction with asterisk symbol to represent the non-intersection words
                    for index in asterisk_index:
                        final_abstraction.insert(index, '*')
                    self.abstractions[abstraction_id]['abstraction'] = final_abstraction

                    abstraction_id += 1

                # check if abstraction only contains asterisks
                if set(self.abstractions[abstraction_id-1]['abstraction']) == {'*'}:
                    abstraction_id -= 1
                    for index, message in group.iteritems():
                        self.abstractions[abstraction_id] = {'original_id': [index],
                                                             'abstraction': list(message)}
                        abstraction_id += 1

            elif group_length == 1:
                self.abstractions[abstraction_id] = {'original_id': [group.keys()[0]],
                                                     'abstraction': list(group.values()[0])}
                abstraction_id += 1


aa = AutoAbstraction('/home/hudan/Git/labeled-authlog/dataset/illustration/per_day/test.log')
aa.get_abstraction()

abstraction = []
for k, v in aa.abstractions.iteritems():
    abstraction.append(v['abstraction'])

abstraction_sorted = sorted(abstraction, key=itemgetter(0))
for a in abstraction_sorted:
    print ' '.join(a)
