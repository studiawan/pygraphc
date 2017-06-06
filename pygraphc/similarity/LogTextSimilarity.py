from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations
import csv
import multiprocessing


class LogTextSimilarity(object):
    """A class for calculating cosine similarity between a log pair. This class is intended for
       non-graph based clustering method.
    """
    def __init__(self, mode, logtype, logs, clusters, cosine_file=''):
        """The constructor of class LogTextSimilarity.

        Parameters
        ----------
        mode        : str
            Mode of operation, i.e., text and text-h5
        logtype     : str
            Type for event log, e.g., auth, syslog, etc.
        logs        : list
            List of every line of original logs.
        clusters    : dict
            Dictionary of clusters. Key: cluster_id, value: list of log line id.
        """
        self.mode = mode
        self.logtype = logtype
        self.logs = logs
        self.clusters = clusters
        self.events = {}
        self.cosine_file = cosine_file

    def __call__(self, node):
        return self.__write_cosine_csv(node)

    def __write_cosine_csv(self, node):
        csv_file = self.cosine_file + str(node) + '.csv'
        f = open(csv_file, 'wb')
        writer = csv.writer(f)
        for cluster_id, cluster in self.clusters.iteritems():
            row = []
            for c in cluster:
                if node != c:
                    similarity = StringSimilarity.get_cosine_similarity(self.events[node]['tf-idf'],
                                                                        self.events[c]['tf-idf'],
                                                                        self.events[node]['length'],
                                                                        self.events[c]['length'])
                    if similarity > 0:
                        row.append(1 - similarity)
            if row:
                row.append(cluster_id)
                writer.writerow(row)
        f.close()

    def get_cosine_similarity(self):
        """Get cosine similarity from a pair of log lines in a file.

        Returns
        -------
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        """
        preprocess = PreprocessLog(self.logtype)
        preprocess.preprocess_text(self.logs)
        self.events = preprocess.events_text
        cosines_similarity = {}

        if self.mode == 'text':
            # calculate cosine similarity
            for log_pair in combinations(range(preprocess.loglength), 2):
                cosines_similarity[log_pair] = \
                    StringSimilarity.get_cosine_similarity(self.events[log_pair[0]]['tf-idf'],
                                                           self.events[log_pair[1]]['tf-idf'],
                                                           self.events[log_pair[0]]['length'],
                                                           self.events[log_pair[1]]['length'])
            return cosines_similarity

        elif self.mode == 'text-csv':
            # write cosine similarity to csv files
            nodes = range(preprocess.loglength)
            pool = multiprocessing.Pool(processes=3)
            pool.map(self, nodes)
            pool.close()
            pool.join()
