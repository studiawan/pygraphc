
class MyMethod(object):
    def __init__(self, graph, clusters):
        self.graph = graph
        self.clusters = clusters
        self.count_partitions = {}

    def __get_count(self):
        abstraction = []
        for cluster_id, nodes in self.clusters.iteritems():
            if len(nodes) > 1:
                for node_id in nodes:
                    message = self.graph.node[node_id]['preprocessed_event']

                    # get count
                    tokens = message.strip().split()
                    token_count = len(tokens)

                    partition_keys = self.count_partitions.keys()
                    if token_count not in partition_keys:
                        self.count_partitions[token_count] = []
                    self.count_partitions[token_count].append(message)

            elif len(nodes) == 1:
                abstraction[cluster_id] = self.graph.node[nodes[0]]['preprocessed_event']
