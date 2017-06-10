from pygraphc.evaluation.InternalEvaluation import InternalEvaluation
from pygraphc.similarity.LogTextSimilarity import LogTextSimilarity
import pickle
import csv


class PySplunkEvaluation(object):
    def __init__(self, clusters, logs, logtype):
        self.clusters = clusters
        self.logs = logs
        self.logtype = logtype

    def get_pysplunk_internal_evaluation(self):
        lts = LogTextSimilarity('text', self.logtype, self.logs, self.clusters)
        cosine_similarity = lts.get_cosine_similarity()
        silhoutte_index = InternalEvaluation.get_silhoutte_index(self.clusters, 'text', None, cosine_similarity)
        dunn_index = InternalEvaluation.get_dunn_index(self.clusters, 'text', None, cosine_similarity)

        return silhoutte_index, dunn_index


if __name__ == '__main__':
    syslog_config = {
        'clusters_file':
            '/home/hudan/Git/pygraphc/result/PySplunk/forensic-challenge-2010-syslog/all/messages-cluster.pickle',
        'logtype': 'syslog',
        'logfile': '/home/hudan/Git/labeled-authlog/dataset/Honeynet/forensic-challenge-2010/'
                   'forensic-challenge-2010-syslog/all/messages',
        'evaluation_file': '/home/hudan/Git/pygraphc/messages.evaluation.csv'
    }

    kippo_config = {
        'clusters_file': '/home/hudan/Git/pygraphc/2017-02-14.log.pickle',
        'logtype': 'kippo',
        'logfile': '/home/hudan/Git/labeled-authlog/dataset/Kippo/per_day/2017-02-14.log',
        'evaluation_file': '/home/hudan/Git/pygraphc/2017-02-14.log.evaluation.csv'
    }

    ras_config = {
        'clusters_file': '/home/hudan/Git/pygraphc/interprid.log.pickle',
        'logtype': 'raslog',
        'logfile': '/home/hudan/Git/labeled-authlog/dataset/ras/per_day/interprid.log',
        'evaluation_file': '/home/hudan/Git/pygraphc/interprid.log.evaluation.csv'
    }

    auth_config = {
        'clusters_file': '/home/hudan/Git/pygraphc/hofstede.log.pickle',
        'logtype': 'auth',
        'logfile': '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/hofstede.log',
        'evaluation_file': '/home/hudan/Git/pygraphc/hofstede.log.evaluation.csv'
    }

    # change this line to work with other datasets
    config = syslog_config

    # open pickled clusters
    with open(config['clusters_file'], 'rb') as f:
        cluster_result = pickle.load(f)

    # open original logs
    with open(config['logfile'], 'r') as f:
        original_logs = f.readlines()

    # get evaluation
    evaluation = PySplunkEvaluation(cluster_result, original_logs, config['logtype'])
    s, d = evaluation.get_pysplunk_internal_evaluation()

    # open and write result to evaluation file
    f = open(config['evaluation_file'], 'wt')
    writer = csv.writer(f)
    writer.writerow(('file_name', 'silhouette', 'dunn'))
    writer.writerow((config['evaluation_file'].split('/')[-1], s, d))
    f.close()
