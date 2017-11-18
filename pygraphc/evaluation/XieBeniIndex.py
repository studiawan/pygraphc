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
        self.__get_all_cluster_properties()

    def __get_centroid(self, cluster):
        # centroid for a particular cluster
        centroid = ''
        for log_id in cluster:
            centroid += self.preprocessed_logs[log_id]

        return centroid

    def __get_all_cluster_properties(self):
        for cluster_id, log_ids in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(log_ids)
            self.cluster_total_nodes[cluster_id] = len(log_ids)
        self.total_cluster = len(self.clusters.keys())

    @staticmethod
    def __get_distance(source, dest):
        cs = CosineSimilarity()
        distance = cs.get_cosine_similarity(source, dest)
        return distance

    def __get_compactness(self):
        all_distances = []
        for cluster_id, log_ids in self.clusters.iteritems():
            cluster_distances = []
            for log_id in log_ids:
                distance = self.__get_distance(self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id])
                cluster_distances.append(pow(distance, 2))
            all_distances.append(sum(cluster_distances))

        compactness = sum(all_distances)
        return compactness

    def __get_separation(self):
        all_distances = []
        for cluster_id1, cluster_id2 in product(xrange(self.total_cluster), repeat=2):
            distance = self.__get_distance(self.cluster_centroids[cluster_id1], self.cluster_centroids[cluster_id2])
            all_distances.append(pow(distance, 2))

        separation = self.log_length * min(all_distances)
        return separation

    def get_xie_beni(self):
        xb_index = self.__get_separation() / self.__get_compactness()
        return xb_index

