import networkx as nx
from ClusterUtility import ClusterUtility


class ConnectedComponents:
    """This is a class for connected component detection method to cluster event logs [Studiawan2016a]_.

    References
    ----------
    .. [Studiawan2016a] H. Studiawan, B. A. Pratomo, and R. Anggoro, Connected component detection for
                        authentication log clustering, The 2nd International Seminar on Science and Technology,
                        pp. 495-496, 2016.
    """
    def __init__(self, graph):
        """This is a constructor for ConnectedComponent class.

        Parameters
        ----------
        graph : graph
            A graph to be clustered.
        """
        self.graph = graph

    def get_clusters(self):
        """This method find any connected component in a graph.

        A component represents a cluster and each component will be given a cluster identifier.
        This method heavily rely on the cosine similarity threshold to build an edge in a graph.

        Returns
        -------
        clusters : dict[list]
            Dictionary of cluster list, where each list contains index (line number) of event log.
        """
        clusters = {}
        cluster_id = 0
        for components in nx.connected_components(self.graph):
            clusters[cluster_id] = components
            cluster_id += 1

        ClusterUtility.set_cluster_id(self.graph, clusters)

        return clusters
