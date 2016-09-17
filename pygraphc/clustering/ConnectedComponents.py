"""
This is a class for connected component detection method to cluster event logs [STU2016]_.

.. [STU2016] H. Studiawan, B. A. Pratomo, and R. Anggoro, Connected component detection for authentication log
             clustering, in Proceedings of the International Seminar on Science and Technology, 2016, pp. 495-496.
"""
import networkx as nx


class ConnectedComponents:
    def __init__(self, g):
        """
        This is a constructor for ConnectedComponent class

        :param g: a graph to be clustered
        """
        self.g = g

    def get_clusters(self):
        """
        This method find any connected component in a graph. A component represents a cluster and
        each component will be given a cluster identifier.

        :return: Clusters
        :rtype: list[list]. List of cluster list, where each list contains index (line number) of event log.
        """
        clusters = []
        for components in nx.connected_components(self.g):
            clusters.append(components)

        cluster_id = 0
        for cluster in clusters:
            for node in cluster:
                self.g.node[node]['cluster'] = cluster_id
            cluster_id += 1

        return clusters