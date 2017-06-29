import csv
import numpy as np


class DunnIndex(object):
    """Class for calculating Dunn Index.
    """
    def __init__(self, mode, clusters, cosine_file):
        """Constructor of class DunnIndex.

        Parameters
        ----------
        mode        : str
            Mode of clustering method, i.e., graph, text, text-csv.
        clusters    : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        cosine_file : str
            Filename that contains cosine similarity of a node to other nodes per cluster.
        """
        self.mode = mode
        self.clusters = clusters
        self.cosine_file = cosine_file

    def __get_node_distance(self, measurement, intra_cluster, source):
        """Get distance from a node to its neighbor.

        The neighbors can be located in intra-cluster or inter-cluster. The distance means
        edge weight in the graph case. In non-graph clustering method, node is equal with log line id.

        Parameters
        ----------
        measurement     : str
            Mode of measurement, i.e., min, max, avg.
        intra_cluster   : bool
            True: intra-cluster, False: inter-cluster.
        source          : dict
            Source node and source cluster.

        Returns
        -------
        final_distance  : float
            Final distance for a node to intra or inter-cluster.
        """
        if self.mode == 'text-csv':
            source_node, source_cluster = source['source_node'], source['source_cluster']
            final_distance = 0.

            # open csv file
            csv_file = self.cosine_file + str(source_node) + '.csv'
            with open(csv_file, 'rb') as f:
                reader = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)

                # intra cluster distance
                if intra_cluster:
                    for row in reader:
                        if row[-1] == source_cluster:
                            if measurement == 'min':
                                final_distance = np.min(row[:-1])
                            elif measurement == 'max':
                                final_distance = np.max(row[:-1])
                            elif measurement == 'avg':
                                final_distance = np.average(row[:-1])
                            break
                # inter cluster distance
                else:
                    # set up comparison variable
                    avg_distance = []
                    if measurement == 'min':
                        final_distance = 1.
                    elif measurement == 'max' or measurement == 'avg':
                        final_distance = 0.

                    # get distance and check final distance
                    for row in reader:
                        if row[-1] != source_cluster:
                            if measurement == 'min':
                                distance = np.min(row[:-1])
                                if distance < final_distance:
                                    final_distance = distance
                            elif measurement == 'max':
                                distance = np.max(row[:-1])
                                if distance > final_distance:
                                    final_distance = distance
                            elif measurement == 'avg':
                                distance = np.average(row[:-1])
                                if distance != 0:
                                    avg_distance.append(distance)

                    if measurement == 'avg':
                        final_distance = np.min(avg_distance) if avg_distance else 0.

            final_distance = round(final_distance, 3)
            return final_distance

    def __get_compactness(self):
        """Maximum node distance as diameter to show a compactness of a cluster.

        Returns
        -------
        final_compactness   : float
            Diameter or compactness of a cluster.
        """
        compactness = {}
        for cluster_id, cluster in self.clusters.iteritems():
            if len(cluster) == 1:
                compactness[cluster[0]] = 0.
            else:
                for node in cluster:
                    if self.mode == 'text-csv':
                        source = {'source_node': node, 'source_cluster': cluster_id}
                        compactness[node] = self.__get_node_distance('max', True, source)

        max_compactness = np.max(compactness.values())
        if max_compactness == 0. or not compactness:
            final_compactness = 1.
        else:
            final_compactness = max_compactness
        return final_compactness

    def __get_separation(self):
        """Separation or minimum distance between clusters.

        It is actually minimum distance between two nodes in calculated clusters.
        Then, we find the most minimum one for all clusters.

        Returns
        -------
        final_separation    : float
            Minimum distance between all clusters.
        """
        # separation is the most minimum intra cluster distance
        separation = {}
        final_separation = 1.
        for cluster_id, cluster in self.clusters.iteritems():
            if len(cluster) == 1:
                if final_separation <= 1.:
                    pass
            else:
                for node in cluster:
                    source = {'source_node': node, 'source_cluster': cluster_id}
                    distance = self.__get_node_distance('min', False, source)
                    if distance != 0:
                        separation[node] = distance

        final_separation = np.min(separation.values()) if separation else 1.
        return final_separation

    def get_dunn_index(self):
        """Get Dunn index. The basic formula is separation / compactness [Liu2010]_.

        Returns
        -------
        dunn_index  : float
            Dunn index value.

        References
        ----------
        .. [Liu2010] Liu, Y., Li, Z., Xiong, H., Gao, X., & Wu, J. Understanding of internal clustering
                     validation measures. In 2010 IEEE 10th International Conference on Data Mining, pp. 911-916.
        """
        dunn_index = 0.
        if self.mode == 'text-csv':
            try:
                dunn_index = self.__get_separation() / self.__get_compactness()
            except ZeroDivisionError:
                dunn_index = 0.

        return dunn_index
