
class MajorClust(object):
    def __init__(self, graph):
        self.graph = graph

    def get_majorclust(self):
        reclusters = set()
        terminate = False
        while not terminate:
            terminate = True
            for node in self.graph.nodes_iter(data=True):
                initial_cluster = node[1]['cluster']
                current_cluster = self._sub_majorclust(node, g)
                recluster = (node[0], initial_cluster, current_cluster)

                # if has not checked, recluster again
                if initial_cluster != current_cluster and recluster not in reclusters:
                    reclusters.add(recluster)
                    node[1]['cluster'] = current_cluster
                    terminate = False

    def _sub_majorclust(self, node):
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
