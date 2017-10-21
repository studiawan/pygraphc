from orderedset import OrderedSet
from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess


class AutoAbstraction(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.unique_events = []
        self.count_groups = {}
        self.abstractions = {}

    def __get_unique_events(self):
        pp = ParallelPreprocess(self.log_file)
        self.unique_events = pp.get_unique_events()

    def __get_count_groups(self):
        self.__get_unique_events()
        for event_id, attributes in self.unique_events:
            message = attributes['preprocessed_event']

            # get count
            words_split = message.strip().split()
            words_count = len(words_split)

            # we need OrderedSet to preserve order because regular set does not preserve order
            group_keys = self.count_groups.keys()
            if words_count not in group_keys:
                self.count_groups[words_count] = {}
            self.count_groups[words_count][event_id] = OrderedSet(words_split)

    def get_abstraction(self):
        # group messages which has the same word count
        self.__get_count_groups()

        # get common words with intersection as abstraction
        abstraction_id = 0
        for words_count, group in self.count_groups.iteritems():
            group_length = len(group.values())
            if group_length > 1:
                # get abstraction
                # prevent initialization to refer to current group variable. re-initialize with OrderedSet()
                self.abstractions[abstraction_id] = {'original_id': [],
                                                     'abstraction': OrderedSet(group.values()[0])}
                for index, message in group.iteritems():
                    self.abstractions[abstraction_id]['original_id'].append(index)
                    self.abstractions[abstraction_id]['abstraction'].intersection_update(message)

                # check for abstraction that only contains one word
                if len(self.abstractions[abstraction_id]['abstraction']) == 1:
                    for index, message in group.iteritems():
                        self.abstractions[abstraction_id] = {'original_id': [index],
                                                             'abstraction': message}
                        abstraction_id += 1
                else:
                    abstraction_id += 1

            elif group_length == 1:
                self.abstractions[abstraction_id] = {'original_id': [group.keys()[0]],
                                                     'abstraction': group.values()[0]}
                abstraction_id += 1

aa = AutoAbstraction('/home/hudan/Git/labeled-authlog/dataset/illustration/per_day/dec-15.log')
aa.get_abstraction()

for k, v in aa.abstractions.iteritems():
    print k, v
