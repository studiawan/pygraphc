from orderedset import OrderedSet


class MyMethod(object):
    def __init__(self, graph, clusters):
        self.graph = graph
        self.clusters = clusters
        self.count_groups = {}

    def get_abstraction(self):
        abstraction = {}
        abstraction_id = 0
        for cluster_id, nodes in self.clusters.iteritems():
            nodes = list(nodes)
            if len(nodes) > 1:
                # group the preprocessed event with the same word count
                for node_id in nodes:
                    message = self.graph.node[node_id]['preprocessed_event']

                    # get count
                    words_split = message.strip().split()
                    words_count = len(words_split)

                    group_keys = self.count_groups.keys()
                    if words_count not in group_keys:
                        self.count_groups[words_count] = []
                    self.count_groups[words_count].append(OrderedSet(words_split))

                # get common words as abstraction
                for words_count, group in self.count_groups.iteritems():
                    abstraction[abstraction_id] = group[0]
                    for message in group:
                        abstraction[abstraction_id].intersection_update(message)
                    abstraction_id += 1

            elif len(nodes) == 1:
                abstraction[abstraction_id] = self.graph.node[nodes[0]]['preprocessed_event']
                abstraction_id += 1

        return abstraction
