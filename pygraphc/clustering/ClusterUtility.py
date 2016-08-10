from itertools import combinations
from operator import itemgetter


class ClusterUtility(object):
    @staticmethod
    def get_geometric_mean(weights):
        multiplication = 1
        for weight in weights:
            multiplication = multiplication * weight

        gmean = 0.0
        if multiplication > 0.0:
            k = float(len(weights))
            gmean = multiplication ** (1 / k)

        return round(gmean, 5)

    @staticmethod
    def get_weighted_cliques(graph, cliques, threshold):
        weighted_kcliques = []
        for clique in cliques:
            weights = []
            for u, v in combinations(clique, 2):
                reduced_precision = round(graph[u][v][0]['weight'], 5)
                weights.append(reduced_precision)
            gmean = ClusterUtility.get_geometric_mean(weights)
            print clique, gmean

            if gmean > threshold:
                weighted_kcliques.append(frozenset(clique))

        return weighted_kcliques

    @staticmethod
    def set_cluster_id(graph, clusters):
        cluster_id = 0
        for cluster in clusters:
            for node in cluster:
                graph.node[node]['cluster'] = cluster_id
            cluster_id += 1

    @staticmethod
    def get_unique_cluster(graph):
        # get unique cluster
        cluster = [n[1]['cluster'] for n in graph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)

        return unique_cluster

    @staticmethod
    def set_cluster_label_id(graph, logs):
        new_cluster_label = {}
        cluster_labels = ['accepted password', 'accepted publickey', 'authentication failure', 'check pass',
                          'connection closed', 'connection reset by peer', 'did not receive identification string',
                          'failed password', 'ignoring max retries', 'invalid user', 'pam adding faulty module',
                          'pam unable to dlopen', 'possible break-in attempt', 'received disconnect', 'received signal',
                          'server listening', 'session closed', 'session opened', 'unknown option']
        unique_cluster = ClusterUtility.get_unique_cluster(graph)
        for uc in unique_cluster:
            for node in graph.nodes_iter(data=True):
                # get all logs per cluster
                if node[1]['cluster'] == uc:
                    members = node[1]['member']
                    logs_per_cluster = []
                    for member in members:
                        logs_per_cluster.append(logs[member])

                    # get dominant label in cluster
                    label_counter = dict((cl, 0) for cl in cluster_labels)
                    for label in cluster_labels:
                        for log in logs_per_cluster:
                            if label in log:
                                label_counter[label] += 1

                    # get most dominant cluster label
                    dominant_cluster_label = sorted(label_counter.items(), key=itemgetter(1), reverse=True)[0][1]
                    new_cluster_label[node[0]] = dominant_cluster_label

        # set new cluster label
        for node_id, new_label in new_cluster_label.iteritems():
            graph.node[node_id]['cluster'] = new_label