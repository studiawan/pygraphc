from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.similarity.StringSimilarity import StringSimilarity
from itertools import combinations
import csv
import multiprocessing


class CalculateMasterSimilarity(object):
    def __init__(self, mode, logtype, logs, clusters, cosine_master_file=''):
        self.mode = mode
        self.logtype = logtype
        self.logs = logs
        self.clusters = clusters
        self.cosine_master_file = cosine_master_file
        self.events = {}
        self.loglength = 0

    def __call__(self, source):
        return self.__write_cosine_csv(source)

    def __write_cosine_csv(self, source):
        # write cosine similarity to csv files
        csv_file = self.cosine_master_file + str(source) + '.csv'
        f = open(csv_file, 'wb')
        writer = csv.writer(f)
        for src, dst in combinations(xrange(self.loglength), 2):
            if src == source:
                similarity = StringSimilarity.get_cosine_similarity(self.events[src]['tf-idf'],
                                                                    self.events[dst]['tf-idf'],
                                                                    self.events[src]['length'],
                                                                    self.events[dst]['length'])
                if similarity > 0:
                    row = [dst, 1 - similarity]
                    writer.writerow(row)
        f.close()

    def calculate_master(self):
        # preprocess event log
        preprocess = PreprocessLog(self.logtype)
        preprocess.preprocess_text(self.logs)
        self.events = preprocess.events_text
        self.loglength = preprocess.loglength

        if self.mode == 'text-csv':
            # calculate cosine similarity in parallel
            nodes = range(preprocess.loglength)
            pool = multiprocessing.Pool(processes=3)
            pool.map(self, nodes)
            pool.close()
            pool.join()
