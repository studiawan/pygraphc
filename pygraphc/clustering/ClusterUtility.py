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
    def set_cluster_label_id(graph, clusters, original_logs, analysis_dir):
        new_cluster_member_label = {}   # store individiual cluster id for each cluster member
        dominant_cluster_labels = {}    # store dominant cluster label from all clusters
        cluster_labels = ['accepted password', 'accepted publickey', 'authentication failure', 'check pass',
                          'connection closed', 'connection reset by peer', 'did not receive identification string',
                          'failed password', 'ignoring max retries', 'invalid user', 'pam adding faulty module',
                          'pam unable to dlopen', 'received disconnect', 'received signal',
                          'reverse mapping checking getaddrinfo', 'server listening', 'session closed',
                          'session opened', 'this does not map back to the address', 'unknown option']
        max_cluster_id = len(cluster_labels) - 1

        for cluster in clusters:
            logs_per_cluster = []
            label_counter = dict((cl, 0) for cl in cluster_labels)
            for c in cluster:
                # get all original_logs per cluster
                members = graph.node[c]['member']
                for member in members:
                    logs_per_cluster.append(original_logs[member])

                # get dominant label in cluster
                for label in cluster_labels:
                    for log in logs_per_cluster:
                        if label in log.lower():
                            label_counter[label] += 1

            # get most dominant cluster label
            dominant_label_counter = sorted(label_counter.items(), key=itemgetter(1), reverse=True)

            # if cluster label has already used
            if dominant_label_counter[0][0] in [labels[0] for labels in dominant_cluster_labels.values()]:
                # get existing counter
                existing_counter = 0
                for ec in dominant_cluster_labels.values():
                    if ec[0] == dominant_label_counter[0][0]:
                        existing_counter = ec[1]

                # check for which one is more dominant
                if dominant_label_counter[0][1] > existing_counter:
                    # get existing cluster with lower existing counter
                    existing_cluster = \
                        dominant_cluster_labels.keys()[dominant_cluster_labels.values().index(existing_counter)]
                    for c in cluster:
                        new_cluster_member_label[c] = cluster_labels.index(dominant_label_counter[0][0])
                    # set old cluster to max_cluster_id + 1
                    for c in existing_cluster:
                        new_cluster_member_label[c] = max_cluster_id + 1

                else:
                    for c in cluster:
                        new_cluster_member_label[c] = max_cluster_id + 1
            # if cluster label has not used
            else:
                dominant_cluster_labels[frozenset(cluster)] = dominant_label_counter[0]
                for c in cluster:
                    new_cluster_member_label[c] = cluster_labels.index(dominant_label_counter[0][0])

        # set new cluster label
        for node_id, new_label in new_cluster_member_label.iteritems():
            graph.node[node_id]['cluster'] = new_label

        # write clustering result to file (clustering result for all members in a node)
        fopen = open(analysis_dir, 'w')
        for key, value in new_cluster_member_label.iteritems():
            cluster_members = graph.node[key]['member']
            for member in cluster_members:
                cluster_label = 'undefined' if value > max_cluster_id else cluster_labels[value]
                fopen.write(str(value) + '; ' + cluster_label + '; ' + original_logs[member])
        fopen.close()