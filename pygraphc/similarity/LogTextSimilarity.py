from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations


class LogTextSimilarity(object):
    """A class for calculating cosine similarity between a log pair. This class is intended for
       non-graph based clustering method.
    """
    def __init__(self, logtype, logs):
        """The constructor of class LogTextSimilarity.

        Parameters
        ----------
        logtype : str
            Type for event log, e.g., auth, syslog, etc.
        logs    : list
            List of every line of original logs.
        """
        self.logtype = logtype
        self.logs = logs

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

        # calculate cosine similarity
        cosines_similarity = {}
        for log_pair in combinations(range(preprocess.loglength), 2):
            cosines_similarity[log_pair] = StringSimilarity.get_cosine_similarity(events[log_pair[0]]['tf-idf'],
                                                                                  events[log_pair[1]]['tf-idf'],
                                                                                  events[log_pair[0]]['length'],
                                                                                  events[log_pair[1]]['length'])
        return cosines_similarity
