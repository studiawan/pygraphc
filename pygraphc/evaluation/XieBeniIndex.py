from __future__ import division
from pygraphc.similarity.CosineSimilarity import CosineSimilarity
from itertools import product


class XieBeniIndex(object):
    def __init__(self, clusters, preprocessed_logs, log_length):
        self.clusters = clusters
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
        self.total_cluster = 0
        self.distance_buffer = {}

    def __get_centroid(self, cluster):
        # centroid for a particular cluster
        centroid = ''
        for log_id in cluster:
            centroid = centroid + ' ' + self.preprocessed_logs[log_id]

        return centroid

    def __get_all_cluster_properties(self):
        # get cluster properties
        for cluster_id, log_ids in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(log_ids)
            self.cluster_total_nodes[cluster_id] = len(log_ids)
        self.total_cluster = len(self.clusters.keys())

    def __get_distance(self, source, dest):
        # get cosine similarity as distance
        cs = CosineSimilarity()
        distance = cs.get_cosine_similarity(source, dest)
        self.distance_buffer[(source, dest)] = distance

        return distance

    def __check_distance(self, checked_pair):
        # check distance is exist or not
        if checked_pair in self.distance_buffer:
            distance = self.distance_buffer[checked_pair]
        else:
            distance = None

        return distance

    def __get_compactness(self):
        # get intra-cluster distance (compactness)
        all_distances = []
        for cluster_id, log_ids in self.clusters.iteritems():
            cluster_distances = []
            for log_id in log_ids:
                distance = self.__check_distance((self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id]))
                if distance is None:
                    distance = self.__get_distance(self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id])
                cluster_distances.append(pow(distance, 2))

            all_distances.append(sum(cluster_distances))

        compactness = sum(all_distances)
        return compactness

    def __get_separation(self):
        # get inter-cluster distance (separation)
        all_distances = []
        for cluster_id1, cluster_id2 in product(xrange(self.total_cluster), repeat=2):
            distance = self.__check_distance((self.cluster_centroids[cluster_id1], self.cluster_centroids[cluster_id2]))
            if distance is None:
                distance = self.__get_distance(self.cluster_centroids[cluster_id1], self.cluster_centroids[cluster_id2])
            all_distances.append(distance ** 2)

        min_distances = min(all_distances)
        separation = self.log_length * min_distances
        return separation

    def get_xie_beni(self):
        # get Xie-Beni index
        self.__get_all_cluster_properties()
        try:
            xb_index = self.__get_compactness() / self.__get_separation()
        except ZeroDivisionError:
            xb_index = 0.

        return xb_index
