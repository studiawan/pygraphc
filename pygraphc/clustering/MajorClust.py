from ClusterUtility import ClusterUtility


class MajorClust(object):
    """The implementation of MajorClust graph clustering algorithm [1]_.

    References
    ----------
    .. [1] B. Stein and O. Niggemann, On the nature of structure and its identification,
           Proceedings of the 25th International Workshop on Graph-Theoretic Concepts in Computer Science,
           pp. 122-134, 1999.
    """
    def __init__(self, graph):
        self.graph = graph
        self.clusters = {}
        self.cluster_property = {}

    def get_majorclust(self):
        self._majorclust()
        self._get_cluster()
        self.cluster_property = ClusterUtility.get_cluster_property(self.graph, self.clusters)

    def _majorclust(self):
        reclusters = set()
        terminate = False
        while not terminate:
            terminate = True
            for node in self.graph.nodes_iter(data=True):
                initial_cluster = node[1]['cluster']
                current_cluster = self._re_majorclust(node)
                recluster = (node[0], initial_cluster, current_cluster)

                # if has not checked, recluster again
                if initial_cluster != current_cluster and recluster not in reclusters:
                    reclusters.add(recluster)
                    node[1]['cluster'] = current_cluster
                    terminate = False

    def _re_majorclust(self, node):
        # reclustering
        visited_neighbor, visited_neigbor_num, neighbor_weights = {}, {}, {}

        # observe neighboring edges and nodes
        for current_node, neighbor_node, weight in self.graph.edges_iter([node[0]], data='weight'):
            neighbor_weights[neighbor_node] = weight
            visited_neighbor[self.graph.node[neighbor_node]['cluster']] = \
                visited_neighbor.get(self.graph.node[neighbor_node]['cluster'], 0.0) + weight['weight']

        # get the weight
        for k, v in visited_neighbor.iteritems():
            visited_neigbor_num.setdefault(v, []).append(k)

        # attach a node to the cluster of majority of neighbor nodes
        current_cluster = visited_neigbor_num[max(visited_neigbor_num)][0] if visited_neigbor_num else \
            node[1]['cluster']

        return current_cluster

    def _get_cluster(self):
        cluster = [n[1]['cluster'] for n in self.graph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)
        cluster_id = 0
        for uc in unique_cluster:
            nodes = []
            for node in self.graph.nodes_iter(data='True'):
                if node[1]['cluster'] == uc:
                    nodes.append(node[1]['cluster'])
            self.clusters[cluster_id] = nodes
            cluster_id += 1
