from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations


class LogTextSimilarity(object):
    def __init__(self, logtype, logfile):
        self.logtype = logtype
        self.logfile = logfile

    def get_cosine_similarity(self):
        preprocess = PreprocessLog(self.logtype, self.logfile)
        preprocess.preprocess_text()
        events = preprocess.events_text

        # calculate cosine similarity
        cosines_similarity = {}
        for log_pair in combinations(preprocess.loglength, 2):
            cosines_similarity[log_pair] = StringSimilarity.get_cosine_similarity(events[log_pair[0]]['tf-idf'],
                                                                       events[log_pair[1]]['tf-idf'],
                                                                       events[log_pair[0]]['length'],
                                                                       events[log_pair[1]]['length'])
        return cosines_similarity
