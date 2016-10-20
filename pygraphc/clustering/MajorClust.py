from operator import itemgetter
from pygraphc.clustering.ClusterAbstraction import ClusterAbstraction
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph


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
        self.visited_neigbor_num = {}
        self.neighbor_weights = {}
        self.current_cluster = 0

    def get_majorclust(self):
        self._majorclust()
        self._get_cluster()

        return self.clusters

    def _majorclust(self):
        reclusters = set()
        terminate = False
        while not terminate:
            terminate = True
            for node in self.graph.nodes_iter(data=True):
                initial_cluster = node[1]['cluster']
                self._re_majorclust(node)
                recluster = (node[0], initial_cluster, self.current_cluster)

                # if has not checked, recluster again
                if initial_cluster != self.current_cluster and recluster not in reclusters:
                    reclusters.add(recluster)
                    node[1]['cluster'] = self.current_cluster
                    terminate = False

    def _re_majorclust(self, node):
        # reclustering
        visited_neighbor = {}

        # observe neighboring edges and nodes
        for current_node, neighbor_node, weight in self.graph.edges_iter([node[0]], data='weight'):
            self.neighbor_weights[neighbor_node] = weight
            visited_neighbor[self.graph.node[neighbor_node]['cluster']] = \
                visited_neighbor.get(self.graph.node[neighbor_node]['cluster'], 0.0) + weight['weight']

        # get the weight
        for k, v in visited_neighbor.iteritems():
            self.visited_neigbor_num.setdefault(v, []).append(k)

        # attach a node to the cluster of majority of neighbor nodes
        self.current_cluster = self.visited_neigbor_num[max(self.visited_neigbor_num)][0] \
            if self.visited_neigbor_num else node[1]['cluster']

    def _get_cluster(self):
        unique_cluster = self._get_unique_cluster()
        cluster_id = 0
        for uc in unique_cluster:
            nodes = []
            for node in self.graph.nodes_iter(data='True'):
                if node[1]['cluster'] == uc:
                    nodes.append(node[1]['cluster'])
            self.clusters[cluster_id] = nodes
            cluster_id += 1

    def _get_unique_cluster(self):
        cluster = [n[1]['cluster'] for n in self.graph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)

        return unique_cluster


class ImprovedReMajorClust(MajorClust):
    def __init__(self, graph):
        super(ImprovedReMajorClust, self).__init__(graph)

    def _re_majorclust(self, node):
        super(ImprovedReMajorClust, self)._re_majorclust(node)
        # re-evaluation
        # 1. a node must be attached to the same cluster as heaviest neighbor node
        if self.visited_neigbor_num:
            heaviest_neighbor_node = sorted(self.neighbor_weights.items(), key=itemgetter(1), reverse=True)[0][0]
            heaviest_neighbor_cluster = self.graph.node[heaviest_neighbor_node]['cluster']
            if self.current_cluster != heaviest_neighbor_cluster:
                self.current_cluster = heaviest_neighbor_cluster


class ImprovedMajorClust(object):
    def __init__(self, graph):
        self.graph = graph

    def get_improved_majorclust(self):
        # run majorclust
        imc = ImprovedReMajorClust(self.graph)
        imc.get_majorclust()

        # create new graph for refined_nodes and create edges
        refined_nodes = self._refine_cluster()
        refined_graph = CreateGraph(refined_nodes, 0)
        refined_graph.do_create()
        rgraph = refined_graph.get_graph()

        # run improved majorclust
        improved_majorclust = ImprovedReMajorClust(rgraph)
        clusters = improved_majorclust.get_majorclust()

        return clusters

    def _refine_cluster(self):
        # set event, cluster id, and its frequency for every cluster
        # a cluster is now represented as a node
        cluster = [n[1]['cluster'] for n in self.graph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)
        refined_nodes = []
        all_events = []

        for uc in unique_cluster:
            events = []
            member = []
            total_frequency, total_nodes = 0, 0
            timestamps = []
            for node in self.graph.nodes_iter(data=True):
                if node[1]['cluster'] == uc:
                    events.append(node[1]['event'])
                    total_frequency += node[1]['frequency']
                    total_nodes += 1
                    timestamps.append(node[1]['start'])
                    timestamps.append(node[1]['end'])
                    member.append(node[0])

            # get start and end time for a specific cluster
            sorted_timestamps = sorted(timestamps)

            # get multiple longest common substring for refined cluster label
            event_lcs = ClusterAbstraction.lcs(events) if len(events) > 1 else events[0]
            refined_nodes.append([uc, {'event': event_lcs.strip(), 'tf-idf': 0, 'length': 0, 'cluster': uc,
                                       'frequency': total_frequency, 'total_nodes': total_nodes, 'status': '',
                                       'start': sorted_timestamps[0], 'end': sorted_timestamps[-1], 'member': member}])
            all_events.append(event_lcs)

        # set tf-idf and document length for refined_nodes
        preprocess = PreprocessLog(None)
        for uc in unique_cluster:
            for node in refined_nodes:
                if node[0] == uc:
                    preprocessed_events, tfidf = preprocess.get_tfidf(node[1]['event'], float(len(all_events)), all_events)
                    if not tfidf:
                        # print node[1]['event']
                        pass
                    node[1]['tf-idf'] = tfidf
                    node[1]['length'] = preprocess.get_doclength(tfidf)

        return refined_nodes
