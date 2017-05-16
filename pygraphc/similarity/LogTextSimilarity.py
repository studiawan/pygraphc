from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations
import networkx as nx
import csv


class LogTextSimilarity(object):
    """A class for calculating cosine similarity between a log pair. This class is intended for
       non-graph based clustering method.
    """
    def __init__(self, mode, logtype, logs, clusters, h5file=''):
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
        h5file      : str
            File name for h5 file to save cosine similarity result.
        """
        self.mode = mode
        self.logtype = logtype
        self.logs = logs
        self.clusters = clusters
        self.h5file = h5file

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
        events = preprocess.events_text
        cosines_similarity = {}

        if self.mode == 'text':
            # calculate cosine similarity
            for log_pair in combinations(range(preprocess.loglength), 2):
                cosines_similarity[log_pair] = StringSimilarity.get_cosine_similarity(events[log_pair[0]]['tf-idf'],
                                                                                      events[log_pair[1]]['tf-idf'],
                                                                                      events[log_pair[0]]['length'],
                                                                                      events[log_pair[1]]['length'])
            return cosines_similarity

        elif self.mode == 'text-csv':
            print self.mode
            for nodex in xrange(preprocess.loglength):
                csv_file = '/tmp/cosine-' + str(nodex) + '.csv'
                f = open(csv_file, 'wb')
                writer = csv.writer(f)

                for cluster_id, cluster in self.clusters.iteritems():
                    row = []
                    for c in cluster:
                        if nodex != c:
                            similarity = StringSimilarity.get_cosine_similarity(events[nodex]['tf-idf'],
                                                                                events[c]['tf-idf'],
                                                                                events[nodex]['length'],
                                                                                events[c]['length'])
                            # if similarity > 0:
                            row.append(1 - similarity)
                    if row:
                        row.append(cluster_id)
                        writer.writerow(row)
                f.close()
