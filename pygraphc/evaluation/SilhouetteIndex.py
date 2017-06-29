import csv
import numpy as np


class SilhouetteIndex(object):
    """Class for calculating Silhouette Index for cluster internal evaluation.
    """
    def __init__(self, mode, clusters, cosine_file):
        """Constructor of class SilhouetteIndex

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

            return round(final_distance, 3)

    def __get_node_silhouette(self):
        """Get node silhoutte.

        Returns
        -------
        node_silhouttes : dict[int, float]
            A dictionary containing silhoutte per node. Key: node identifier, value: silhoutte.
        """
        node_silhouettes = {}
        for cluster_id, cluster in self.clusters.iteritems():
            if len(cluster) == 1:
                node_silhouettes[cluster[0]] = 1
            else:
                for node in cluster:
                    if self.mode == 'text-csv':
                        try:
                            source = {'source_node': node, 'source_cluster': cluster_id}
                            intercluster_avg = self.__get_node_distance('avg', False, source)
                            intracluster_avg = self.__get_node_distance('avg', True, source)
                            node_silhouettes[node] = (intercluster_avg - intracluster_avg) / \
                                max(intercluster_avg, intracluster_avg)
                        except ZeroDivisionError:
                            node_silhouettes[node] = 0.

        return node_silhouettes

    def __get_cluster_silhouette(self):
        """Get cluster silhoutte.

        Returns
        -------
        cluster_silhouttes  : dict[int, float]
            A dictionary containing silhoutte per cluster. Key: cluster identifier, value: silhoutte.
        """
        node_silhouettes, cluster_silhouettes = {}, {}
        if self.mode == 'text-csv':
            node_silhouettes = self.__get_node_silhouette()

        for cluster_id, cluster in self.clusters.iteritems():
            silhoutte = []
            for node in cluster:
                silhoutte.append(node_silhouettes[node])
            cluster_silhouettes[cluster_id] = np.average(silhoutte) if silhoutte else -1.

        return cluster_silhouettes

    def get_silhouette_index(self):
        """Get silhoutte index for a graph [Almeida2011]_.

        Returns
        -------
        silhoutte_index : float
            The silhoutte index for a graph.

        References
        ----------
        .. [Almeida2011] Helio Almeida, Dorgival Guedes, Wagner Meira Jr, and Mohammed J. Zaki.
                         "Is there a best quality metric for graph clusters?."
                         In Joint European Conference on Machine Learning and Knowledge Discovery in Databases,
                         pp. 44-59. Springer Berlin Heidelberg, 2011.
        """
        cluster_silhouettes = {}
        if self.mode == 'text-csv':
            cluster_silhouettes = self.__get_cluster_silhouette()

        silhoutte_index = np.average(cluster_silhouettes.values()) if cluster_silhouettes else -1.
        return silhoutte_index
