from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations
from tables import *
import operator as op


class LogTextSimilarity(object):
    """A class for calculating cosine similarity between a log pair. This class is intended for
       non-graph based clustering method.
    """
    def __init__(self, mode, logtype, logs, h5file=''):
        """The constructor of class LogTextSimilarity.

        Parameters
        ----------
        mode    : str
            Mode of operation, i.e., text and text-h5
        logtype : str
            Type for event log, e.g., auth, syslog, etc.
        logs    : list
            List of every line of original logs.
        h5file  : str
            File name for h5 file to save cosine similarity result.
        """
        self.mode = mode
        self.logtype = logtype
        self.logs = logs
        self.h5file = h5file

    @staticmethod
    def __ncr(n, r):
        """Calculate total of combinations nCr.

        Parameters
        ----------
        n   : float
            Numerator.
        r   : float
            Denumerator.

        Returns
        -------
        total   : float
            Total combinations.

        Notes
        -----
        http://stackoverflow.com/questions/4941753/is-there-a-math-ncr-function-in-python
        """
        r = min(r, n - r)
        if r == 0:
            return 1

        numer = reduce(op.mul, xrange(n, n - r, -1))
        denom = reduce(op.mul, xrange(1, r + 1))
        total = numer // denom
        return total

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

        elif self.mode == 'text-h5':
            # h5 configuration for cosine similarity
            class Cosine(IsDescription):
                source = Int32Col()
                dest = Int32Col()
                similarity = Float32Col()

            # get combinations
            total_combination = self.__ncr(preprocess.loglength, 2)
            h5filter = Filters(complib='zlib', complevel=1)
            h5cosine_file = open_file(self.h5file, mode='w', title='Cosine similarity')
            h5group = h5cosine_file.create_group("/", 'cosine_group', 'Cosine similarity group')
            h5table = h5cosine_file.create_table(h5group, 'cosine_table', Cosine, "Cosine similarity table",
                                                 filters=h5filter, expectedrows=total_combination)
            h5cosine = h5table.row

            # calculate cosine similarity
            for log_pair in combinations(xrange(preprocess.loglength), 2):
                cosines_similarity[log_pair] = StringSimilarity.get_cosine_similarity(events[log_pair[0]]['tf-idf'],
                                                                                      events[log_pair[1]]['tf-idf'],
                                                                                      events[log_pair[0]]['length'],
                                                                                      events[log_pair[1]]['length'])
                h5cosine['source'] = log_pair[0]
                h5cosine['dest'] = log_pair[1]
                h5cosine['similarity'] = cosines_similarity[log_pair]
                h5cosine.append()

            # write to file and then close
            h5table.cols.source.create_csindex()
            h5table.cols.dest.create_csindex()
            h5table.flush()
            h5cosine_file.close()
