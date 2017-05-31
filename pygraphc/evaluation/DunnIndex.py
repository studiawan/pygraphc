import csv
import numpy as np


class DunnIndex(object):
    def __init__(self, mode, clusters, cosine_file):
        self.mode = mode
        self.clusters = clusters
        self.cosine_file = cosine_file

    def __get_node_distance(self, measurement, intra_cluster, source):
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

    def __get_compactness(self):
        compactness = {}
        for cluster_id, cluster in self.clusters.iteritems():
            if len(cluster) == 1:
                compactness[cluster[0]] = 0.
            else:
                for node in cluster:
                    if self.mode == 'text-csv':
                        source = {'source_node': node, 'source_cluster': cluster_id}
                        compactness[node] = self.__get_node_distance('max', True, source)

        final_compactness = np.max(compactness.values()) if compactness else 0.
        return final_compactness

    def __get_separation(self):
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
        dunn_index = 0.
        if self.mode == 'text-csv':
            dunn_index = self.__get_separation() / self.__get_compactness()

        return dunn_index
