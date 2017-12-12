from __future__ import division
from orderedset import OrderedSet
from pygraphc.similarity.CosineSimilarity import CosineSimilarity
from itertools import combinations, product


class DaviesBouldinIndex(object):
    def __init__(self, clusters, preprocessed_logs, log_length):
        self.clusters = clusters
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
        self.total_cluster = 0
        self.distance_buffer = {}

    def __get_centroid(self, cluster=None):
        centroid = ''

        # centroid for a particular cluster
        if cluster:
            for log_id in cluster:
                if centroid == '':
                    centroid = self.preprocessed_logs[log_id]
                else:
                    centroid = ' '.join([centroid, self.preprocessed_logs[log_id]])
        # centroid for the whole logs
        else:
            for log_id in self.preprocessed_logs:
                if centroid == '':
                    centroid = self.preprocessed_logs[log_id]
                else:
                    centroid = ' '.join([centroid, self.preprocessed_logs[log_id]])

        centroid = OrderedSet(centroid.split())
        centroid = ' '.join(list(centroid))
        return centroid

    def __get_all_cluster_properties(self):
        # get cluster properties
        for cluster_id, log_ids in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(log_ids)
            self.cluster_total_nodes[cluster_id] = len(log_ids)
        self.total_cluster = len(self.clusters.keys())

    def __get_distance(self, source, dest):
        # get cosine similarity as distance
        if source == dest:
            distance = 0.1
        else:
            cs = CosineSimilarity()
            distance = 1 - cs.get_cosine_similarity(source, dest)
        self.distance_buffer[(source, dest)] = distance

        return round(distance, 3)

    def __check_distance(self, checked_pair):
        # check distance is exist or not
        if checked_pair in self.distance_buffer:
            distance = self.distance_buffer[checked_pair]
        else:
            distance = None

        return distance

    def __get_dispersion(self):
        # get cluster dispersion (intra-cluster compactness)
        cluster_dispersions = {}
        for cluster_id, log_ids in self.clusters.iteritems():
            distances = []
            for log_id in log_ids:
                distance = self.__check_distance((self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id]))
                if distance is None:
                    distance = self.__get_distance(self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id])
                distances.append(round(distance, 3))
            total_distance = sum(distances)

            try:
                cluster_dispersions[cluster_id] = 1 / self.cluster_total_nodes[cluster_id] * total_distance
            except ZeroDivisionError:
                cluster_dispersions[cluster_id] = 0.

        return cluster_dispersions

    def __get_dissimilarity(self):
        # get cluster dissimilarity (inter-cluster separation)
        cluster_dissimilarity = {}
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            distance = self.__check_distance((self.cluster_centroids[cluster_id1], self.cluster_centroids[cluster_id2]))
            if distance is None:
                distance = self.__get_distance(self.cluster_centroids[cluster_id1], self.cluster_centroids[cluster_id2])
            cluster_dissimilarity[(cluster_id1, cluster_id2)] = round(distance, 3)

        return cluster_dissimilarity

    def __get_similarity(self):
        # get similarity (ratio between compactness and separation)
        similarity = {}
        cluster_dispersions = self.__get_dispersion()
        cluster_dissimilarity = self.__get_dissimilarity()
        for cluster_id1, cluster_id2 in combinations(xrange(self.total_cluster), 2):
            try:
                sim = (cluster_dispersions[cluster_id1] + cluster_dispersions[cluster_id2]) / \
                      cluster_dissimilarity[(cluster_id1, cluster_id2)]
                similarity[(cluster_id1, cluster_id2)] = round(sim, 3)
            except ZeroDivisionError:
                similarity[(cluster_id1, cluster_id2)] = 0.

        return similarity

    def __get_r(self):
        # get R
        r = {}
        similarity = self.__get_similarity()
        similarity_keys = similarity.keys()
        for cluster_id, log_ids in self.clusters.iteritems():
            r_cluster = []
            for cluster_id1, cluster_id2 in product(xrange(self.total_cluster), repeat=2):
                if cluster_id == cluster_id1 and cluster_id1 != cluster_id2:
                    if (cluster_id1, cluster_id2) in similarity_keys:
                        r_cluster.append(similarity[(cluster_id1, cluster_id2)])
                    else:
                        r_cluster.append(similarity[(cluster_id2, cluster_id1)])
            r[cluster_id] = max(r_cluster)

        return r

    def get_davies_bouldin(self):
        # get Davies-Bouldin index
        # print 'cluster length', len(self.clusters)
        if len(self.clusters) not in [0, 1]:
            self.__get_all_cluster_properties()
            r = self.__get_r()
            try:
                db_index = 1 / self.total_cluster * sum(r.values())
            except ZeroDivisionError:
                db_index = 0.
        else:
            db_index = 0.

        return round(db_index, 3)
