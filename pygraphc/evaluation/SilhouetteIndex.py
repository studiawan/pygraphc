import csv
import numpy as np


class SilhouetteIndex(object):
    def __init__(self, mode, clusters):
        """Calculate Silhouette index for cluster internal evaluation.

        Parameters
        ----------
        mode        : str
        clusters    : dict
        """
        self.mode = mode
        self.clusters = clusters

    def __get_node_distance(self, measurement, intra_cluster, source):
        if self.mode == 'text-csv':
            source_node, source_cluster = source['source_node'], source['source_cluster']
            final_distance = 0.

            # open csv file
            csv_file = '/tmp/cosine-' + str(source_node) + '.csv'
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
        node_silhouettes = {}
        for cluster_id, cluster in self.clusters.iteritems():
            if len(cluster) == 1:
                node_silhouettes[cluster[0]] = 1
            else:
                for node in cluster:
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
        cluster_silhouettes = {}
        if self.mode == 'text-csv':
            cluster_silhouettes = self.__get_cluster_silhouette()

        silhoutte_index = np.average(cluster_silhouettes.values()) if cluster_silhouettes else -1.
        return silhoutte_index
