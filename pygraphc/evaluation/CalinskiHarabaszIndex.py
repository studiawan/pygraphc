from __future__ import division
from orderedset import OrderedSet
from pygraphc.similarity.CosineSimilarity import CosineSimilarity


class CalinskiHarabaszIndex(object):
    def __init__(self, clusters, preprocessed_logs, log_length):
        self.clusters = clusters
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
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

    def __get_trace_b(self):
        # get trace B
        traces_b = []
        logs_centroid = self.__get_centroid()
        for cluster_id, log_ids in self.clusters.iteritems():
            distance = self.__check_distance((self.cluster_centroids[cluster_id], logs_centroid))
            if distance is None:
                distance = self.__get_distance(self.cluster_centroids[cluster_id], logs_centroid)

            trace_b = self.cluster_total_nodes[cluster_id] * (distance ** 2)
            traces_b.append(trace_b)

        total_trace_b = sum(traces_b)
        return round(total_trace_b, 3)

    def __get_trace_w(self):
        # get trace W
        traces_w = []
        for cluster_id, log_ids in self.clusters.iteritems():
            trace_w_cluster = []
            for log_id in log_ids:
                distance = self.__check_distance((self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id]))
                if distance is None:
                    distance = self.__get_distance(self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id])

                trace_w = distance ** 2
                trace_w_cluster.append(trace_w)
            traces_w.append(sum(trace_w_cluster))

        total_traces_w = sum(traces_w)
        return round(total_traces_w, 3)

    def get_calinski_harabasz(self):
        # get Calinski-Harbasz index
        self.__get_all_cluster_properties()
        total_cluster = len(self.clusters.keys())

        try:
            ch_index = (self.__get_trace_b() / (total_cluster - 1)) / \
                       (self.__get_trace_w() / (self.log_length - total_cluster))
        except ZeroDivisionError:
            ch_index = 0.

        return round(ch_index, 3)
