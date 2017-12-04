from operator import itemgetter
from pygraphc.abstraction.ClusterAbstraction import ClusterAbstraction
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.preprocess.PreprocessLog import PreprocessLog


class MajorClust(object):
    """The implementation of MajorClust graph clustering algorithm [Stein1999]_.

    References
    ----------
    .. [Stein1999] B. Stein and O. Niggemann, On the nature of structure and its identification,
                   Proceedings of the 25th International Workshop on Graph-Theoretic Concepts in Computer Science,
                   pp. 122-134, 1999.
    """
    def __init__(self, graph):
        """The constructor of class MajorClust.

        Parameters
        ----------
        graph   : graph
            A graph to be clustered.
        """
        self.graph = graph
        self.clusters = {}

    def get_majorclust(self, graph):
        """The main method to run MajorClust algorithm.

        Parameters
        ----------
        graph   : graph
            A graph to be clustered.

        Returns
        -------
        clusters = dict[list]
            Dictionary of list containing node identifier for each cluster.
        """
        # run majorclust algorithm
        self._majorclust(graph)
        self._get_cluster()

        return self.clusters

    def _majorclust(self, graph):
        """The main procedure of MajorClust which is visiting every node to be evaluated for its neighbor cluster.

        Parameters
        ----------
        graph   : graph
            A graph to be clustered. It can be original graph or the refined one.
        """
        reclusters = set()
        terminate = False
        while not terminate:
            terminate = True
            for node in graph.nodes_iter(data=True):
                initial_cluster = node[1]['cluster']
                current_cluster = self._re_majorclust(node, graph)
                recluster = (node[0], initial_cluster, current_cluster)

                # if has not checked, recluster again
                if initial_cluster != current_cluster and recluster not in reclusters:
                    reclusters.add(recluster)
                    node[1]['cluster'] = current_cluster
                    terminate = False

    def _re_majorclust(self, node, graph):
        """Evaluating the neighbor nodes.

        Parameters
        ----------
        node    : node
            A node in a processed graph.
        graph   : graph
            A graph to be clustered. It can be original graph or the refined one.
        """
        # reclustering
        visited_neighbor, visited_neigbor_num, neighbor_weights = {}, {}, {}

        # observe neighboring edges and nodes
        for current_node, neighbor_node, weight in graph.edges_iter([node[0]], data='weight'):
            neighbor_weights[neighbor_node] = weight
            visited_neighbor[graph.node[neighbor_node]['cluster']] = \
                visited_neighbor.get(graph.node[neighbor_node]['cluster'], 0.0) + weight['weight']

        # get the weight
        for k, v in visited_neighbor.iteritems():
            visited_neigbor_num.setdefault(v, []).append(k)

        # attach a node to the cluster of majority of neighbor nodes
        current_cluster = visited_neigbor_num[max(visited_neigbor_num)][0] \
            if visited_neigbor_num else node[1]['cluster']

        return current_cluster

    def _get_cluster(self):
        """Get cluster in the form of dictionary of node identifier list. The cluster id is in incremental integer.
        """
        unique_cluster = self._get_unique_cluster()
        cluster_id = 0
        for uc in unique_cluster:
            nodes = []
            for node in self.graph.nodes_iter(data='True'):
                if node[1]['cluster'] == uc:
                    nodes.append(node[0])
                    node[1]['cluster'] = cluster_id
            self.clusters[cluster_id] = nodes
            cluster_id += 1

    def _get_unique_cluster(self):
        """Get unique cluster identifier.

        Returns
        -------
        unique_cluster  : set
            A set containing unique cluster identifier.
        """
        cluster = [n[1]['cluster'] for n in self.graph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)

        return unique_cluster


class ImprovedMajorClust(MajorClust):
    """A class that improves MajorClust.

       It improves the method _re_majorclust to have re-evaluation. This procedure then add refine cluster step
       as the re-majorclust provides overvitting clusters.
    """
    def __init__(self, graph):
        """The constructor of class ImprovedMajorClust.

        Parameters
        ----------
        graph   : graph
            A graph to be clustered.
        """
        super(ImprovedMajorClust, self).__init__(graph)
        self.rgraph = None

    def get_improved_majorclust(self):
        """The main method to run improved MajorClust algorithm. The procedure gets the refined nodes and
        call ImprovedMajorClust once again.

        Returns
        -------
        clusters    : dict[list]
            Dictionary of list containing node identifier for each cluster.
        """
        # run majorclust
        super(ImprovedMajorClust, self).get_majorclust(self.graph)

        # create new graph for refined_nodes and create edges
        refined_nodes = self._refine_cluster()
        refined_graph = CreateGraph(refined_nodes, 0)
        refined_graph.do_create()
        self.rgraph = refined_graph.g

        # run improved majorclust with refined graph
        super(ImprovedMajorClust, self).get_majorclust(self.rgraph)
        self._backto_prerefine()
        self.clusters = {}
        super(ImprovedMajorClust, self)._get_cluster()

        # if only one cluster found, then a node become a cluster
        if len(self.clusters) == 1:
            cluster_id = 0
            for node in self.graph.nodes_iter(data=True):
                self.clusters[cluster_id] = [node[0]]
                cluster_id += 1

        return self.clusters

    def get_improved_majorclust_wo_refine(self):
        # run majorclust
        super(ImprovedMajorClust, self).get_majorclust(self.graph)
        self.clusters = {}
        super(ImprovedMajorClust, self)._get_cluster()

        return self.clusters

    def _re_majorclust(self, node, graph):
        """Re-evaluation of a node after clustered by standard MajorClust.

        Parameters
        ----------
        node    : node
            An evaluated node.
        graph   : graph
            A graph to be clustered. It can be original graph or the refined one.
        """
        # reclustering
        visited_neighbor, visited_neigbor_num, neighbor_weights = {}, {}, {}

        # observe neighboring edges and nodes
        for current_node, neighbor_node, weight in graph.edges_iter([node[0]], data='weight'):
            neighbor_weights[neighbor_node] = weight
            visited_neighbor[graph.node[neighbor_node]['cluster']] = \
                visited_neighbor.get(graph.node[neighbor_node]['cluster'], 0.0) + weight['weight']

        # get the weight
        for k, v in visited_neighbor.iteritems():
            visited_neigbor_num.setdefault(v, []).append(k)

        # attach a node to the cluster of majority of neighbor nodes
        current_cluster = visited_neigbor_num[max(visited_neigbor_num)][0] \
            if visited_neigbor_num else node[1]['cluster']

        # set event, cluster id, and its frequency for every cluster
        # a cluster is now represented as a node
        if visited_neigbor_num:
            heaviest_neighbor_node = sorted(neighbor_weights.items(), key=itemgetter(1), reverse=True)[0][0]
            heaviest_neighbor_cluster = graph.node[heaviest_neighbor_node]['cluster']
            if current_cluster != heaviest_neighbor_cluster:
                current_cluster = heaviest_neighbor_cluster

        return current_cluster

    def _refine_cluster(self):
        """Refine cluster by representing a previously generated cluster as a vertex.

        Returns
        -------
        refined_nodes   : list[list]
            List of list containing node identifier and its properties.
        """
        # set event, cluster id, and its frequency for every cluster
        # a cluster is now represented as a node
        unique_cluster = super(ImprovedMajorClust, self)._get_unique_cluster()
        refined_nodes = []
        all_events = []

        for uc in unique_cluster:
            events = []
            member = []
            total_frequency, total_nodes = 0, 0
            timestamps = []
            for node in self.graph.nodes_iter(data=True):
                if node[1]['cluster'] == uc:
                    events.append(node[1]['event'])    # to be tested: not 'event' but 'preprocessed_event'
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
        preprocess = PreprocessLog('auth')
        for uc in unique_cluster:
            for node in refined_nodes:
                if node[0] == uc:
                    preprocessed_events, tfidf = \
                        preprocess.get_tfidf(node[1]['event'], float(len(all_events)), all_events)
                    if not tfidf:
                        # print node[1]['event']
                        pass
                    node[1]['tf-idf'] = tfidf
                    node[1]['length'] = preprocess.get_doclength(tfidf)

        return refined_nodes

    def _backto_prerefine(self):
        """This procedure will convert the result of clustering from refined graph to original graph.
        """
        cluster = [n[1]['cluster'] for n in self.rgraph.nodes_iter(data='cluster')]
        unique_cluster = set(cluster)
        for uc in unique_cluster:
            for node in self.rgraph.nodes_iter(data=True):
                if node[1]['cluster'] == uc:
                    members = node[1]['member']
                    for member in members:
                        self.graph.node[member]['cluster'] = uc
