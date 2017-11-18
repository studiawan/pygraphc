from pygraphc.similarity.CosineSimilarity import CosineSimilarity


class CalinskiHarabaszIndex(object):
    def __init__(self, clusters, preprocessed_logs, log_length):
        self.clusters = clusters
        self.preprocessed_logs = preprocessed_logs
        self.log_length = log_length
        self.cluster_centroids = {}
        self.cluster_total_nodes = {}
        self.__get_all_cluster_properties()

    def __get_centroid(self, cluster=None):
        centroid = ''

        # centroid for a particular cluster
        if cluster:
            for log_id in cluster:
                centroid += self.preprocessed_logs[log_id]
        # centroid for the whole logs
        else:
            for log_id in self.preprocessed_logs:
                centroid += self.preprocessed_logs[log_id]

        return centroid

    def __get_all_cluster_properties(self):
        for cluster_id, log_ids in self.clusters.iteritems():
            self.cluster_centroids[cluster_id] = self.__get_centroid(log_ids)
            self.cluster_total_nodes[cluster_id] = len(log_ids)

    @staticmethod
    def __get_distance(source, dest):
        cs = CosineSimilarity()
        distance = cs.get_cosine_similarity(source, dest)
        return distance

    def __get_trace_b(self):
        traces_b = []
        logs_centroid = self.__get_centroid()
        for cluster_id, log_ids in self.clusters.iteritems():
            trace_b = self.cluster_total_nodes[cluster_id] * \
                      (self.__get_distance(self.cluster_centroids[cluster_id], logs_centroid) ** 2)
            traces_b.append(trace_b)

        total_trace_b = sum(traces_b)
        return total_trace_b

    def __get_trace_w(self):
        traces_w = []
        for cluster_id, log_ids in self.clusters.iteritems():
            trace_w_cluster = []
            for log_id in log_ids:
                trace_w = self.__get_distance(self.preprocessed_logs[log_id], self.cluster_centroids[cluster_id]) ** 2
                trace_w_cluster.append(trace_w)
            traces_w.append(sum(trace_w_cluster))

        total_traces_w = sum(traces_w)
        return total_traces_w

    def get_calinski_harabasz(self):
        total_cluster = len(self.clusters.keys())
        ch_index = (self.__get_trace_b() / (total_cluster - 1)) / \
                   (self.__get_trace_w() / (self.log_length - total_cluster))

        return ch_index

