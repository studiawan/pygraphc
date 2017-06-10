import os
import fnmatch
import csv
import pickle
from time import time
from pygraphc.bin.Experiment import get_dataset, get_external_evaluation, get_internal_evaluation
from pygraphc.similarity.LogTextSimilarity import LogTextSimilarity
from pygraphc.evaluation.SilhouetteIndex import SilhouetteIndex
from pygraphc.evaluation.DunnIndex import DunnIndex
from pygraphc.output.OutputText import OutputText


class PySplunk(object):
    """Get log clustering using Python Splunk API [SplunkDev2016]_.

    References
    ----------
    .. [SplunkDev2016] Command line examples in the Splunk SDK for Python.
                       http://dev.splunk.com/view/python-sdk/SP-CAAAEFK
    """
    def __init__(self, username, password, output_mode, dataset, log_type, source_type, evaluation,
                 tmp_file='/tmp/pysplunk_cluster.csv'):
        """The constructor of class PySplunk.

        Parameters
        ----------
        username        : str
            Username to access Splunk daemon. No password required since we use Splunk free version.
        password        : str
            Password to access Splunk daemon.
        output_mode     : str
            Output for clustering result. Recommended output is csv.
        log_type        : str
            Type of the event log.
        source_type     : str
            Type of the event log for internal Splunk processing.
        evaluation      : str
            Type of clustering evaluation, i.e., internal and external.
        tmp_file        : str
            Path for temporary clustering result.
        """
        self.username = username
        self.password = password
        self.output_mode = output_mode
        self.dataset = dataset
        self.log_type = log_type
        self.source_type = source_type
        self.evaluation = evaluation
        self.tmp_file = tmp_file
        self.logs = []

    def get_splunk_cluster(self, source):
        """Get log clusters.

        Parameters
        ----------
        source      : str
            Identifier for log source. It is usually filename of log.

        Returns
        -------
        clusters    : dict
            Dictionary of log cluster. Key: cluster_id, value: list of log line identifier.
        """
        # run Python Splunk API command
        source = source.replace(' ', '\ ')
        source = source.split('/')[-1]
        command = 'python /home/hudan/Downloads/splunk-sdk-python-1.6.1/examples/search.py ' + \
                  '--host=127.0.0.1 --port=8089 ' + \
                  '--username=' + self.username + ' --password=' + self.password + \
                  ' "search source=' + self.dataset + '-' + source + \
                  ' host=' + self.dataset + ' sourcetype=' + self.source_type + \
                  ' | cluster labelfield=cluster_id labelonly=t |' \
                  ' table cluster_id _raw | sort 0 field _time | reverse" ' + \
                  '--output_mode=' + self.output_mode + " > " + self.tmp_file
        os.system(command)

        # read clusters in temporary file
        with open(self.tmp_file, 'r') as f:
            self.logs = f.readlines()

        # delete first and last element in logs
        del self.logs[0]
        del self.logs[-1]

        # get clusters
        clusters = {}
        for index, log in enumerate(self.logs):
            cluster_id = log.split(',')[0]
            clusters[cluster_id] = clusters.get(cluster_id, []) + [index]

        # remove tmp_file
        os.remove(self.tmp_file)
        return clusters

    def get_bulk_cluster(self):
        # get dataset files
        master_path = '/home/hudan/Git/labeled-authlog/dataset/'
        dataset_path = {
            'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
            'SecRepo': master_path + 'SecRepo/auth-perday',
            'forensic-challenge-2010':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-5-2010-perday',
            'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
            'forensic-challenge-2010-syslog':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all'
        }

        # note that in RedHat-based authentication log, parameter '*.log' is not used
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'PySplunk')

        # open evaluation file
        f = open(evaluation_file, 'wt')
        writer = csv.writer(f)

        # set header
        header = ()
        if self.evaluation == 'external':
            header = ('file_name', 'adjusted_rand', 'adjusted_mutual_info', 'normalized_mutual_info',
                      'homogeneity', 'completeness', 'v-measure')
        elif self.evaluation == 'internal':
            header = ('file_name', 'silhouette', 'dunn')
        writer.writerow(header)

        # main process to cluster log file
        for file_identifier, properties in files.iteritems():
            print file_identifier
            clusters = self.get_splunk_cluster(properties['log_path'])
            original_logs = self.logs
            row = ()

            # evaluate cluster based on its type
            if self.evaluation == 'external':
                ar, ami, nmi, h, c, v = get_external_evaluation(None, clusters, original_logs, properties,
                                                                self.log_type)
                row = ('/'.join(properties['log_path'].split('/')[-2:]), ar, ami, nmi, h, c, v)
            elif self.evaluation == 'internal':
                silhouette, dunn = get_internal_evaluation(None, clusters, original_logs, properties, 'text',
                                                           self.log_type)
                row = ('/'.join(properties['log_path'].split('/')[-2:]), silhouette, dunn)

            # write evaluation result to file
            writer.writerow(row)

        f.close()

    def get_bulk_cluster2(self):
        # get dataset files
        master_path = '/home/hudan/Git/labeled-authlog/dataset/'
        dataset_path = {
            'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
            'SecRepo': master_path + 'SecRepo/auth-perday',
            'forensic-challenge-2010':
                master_path + 'Honeynet/forensic-challenge-5-2010/forensic-challenge-5-2010-perday',
            'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
            'Kippo': master_path + 'Kippo/per_day',
            'forensic-challenge-2010-syslog':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all',
            'BlueGene2006': master_path + 'BlueGene2006/per_day',
            'ras': master_path + 'ras/per_day',
            'illustration': master_path + 'illustration/per_day',
            'vpn': master_path + 'vpn/per_day'
        }

        # note that in RedHat-based authentication log, parameter '*.log' is not used
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'PySplunk')

        for file_identifier, properties in files.iteritems():
            print file_identifier

            # main process to cluster log file
            clusters = self.get_splunk_cluster(properties['log_path'])

            # write clustering result in dictionary to file
            with open(properties['cluster_pickle'], 'wb') as f:
                pickle.dump(clusters, f, protocol=pickle.HIGHEST_PROTOCOL)


class UploadToSplunk(object):
    """Upload log file to Splunk.
    """
    def __init__(self, username, password, dataset, sourcetype):
        """The constructor of class UploadToSplunk.

        Parameters
        ----------
        username    : str
            Username to access Splunk daemon.
        password    : str
            Password to access Splunk daemon.
        dataset     : str
            Dataset type for event log.
        sourcetype  : str
            Type of event log. By default, it is set to 'linux_secure'
        """
        self.username = username
        self.password = password
        self.dataset = dataset
        self.sourcetype = sourcetype

    def single_upload(self, log_path):
        """Upload a single log file to Splunk.

        Parameters
        ----------
        log_path    : str
            Path for log file to be uploaded to Splunk.
        """
        log_path = log_path.replace(' ', '\ ')
        log_file = log_path.split('/')[-1]
        command = 'python /home/hudan/Downloads/splunk-sdk-python-1.6.1/examples/upload.py' + \
                  ' --host=192.168.1.106 --port=8089 ' + \
                  ' --username=' + self.username + ' --password=' + self.password + \
                  ' --sourcetype=' + self.sourcetype + ' --eventhost=' + self.dataset + \
                  ' --source=' + self.dataset + '-' + log_file + ' ' + log_path
        os.system(command)

    def bulk_upload(self):
        """Bulk upload of many event log files to Splunk.
        """
        # get dataset files
        master_path = '/home/hudan/Git/labeled-authlog/dataset/'
        dataset_path = {
            'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
            'SecRepo': master_path + 'SecRepo/auth-perday',
            'forensic-challenge-2010':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-5-2010-perday',
            'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
            'forensic-challenge-2010-syslog':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all'
        }

        # get all log files under dataset directory
        matches = []
        # Debian-based: /var/log/auth.log
        if self.dataset == 'Hofstede2014' or self.dataset == 'SecRepo' or self.dataset == 'forensic-challenge-2010':
            for root, dirnames, filenames in os.walk(dataset_path[self.dataset]):
                for filename in fnmatch.filter(filenames, '*.log'):
                    matches.append(os.path.join(root, filename))
        # RedHat-based: /var/log/secure
        elif self.dataset == 'hnet-hon-2004' or self.dataset == 'hnet-hon-2006' or \
                self.dataset == 'forensic-challenge-2010-syslog':
            file_lists = os.listdir(dataset_path[self.dataset])
            matches = [dataset_path[self.dataset] + '/' + filename
                       for filename in file_lists if not filename.endswith('.labeled')]

        # upload to Splunk
        for match in matches:
            print match
            self.single_upload(match)


class DeleteFromSplunk(object):
    """Delete log from Splunk to avoid duplicates after re-indexing.
    """
    def __init__(self, username, password, dataset):
        """Constructor for class DeleteFromSplunk.

        Parameters
        ----------
        username    : str
            Username to access Splunk daemon.
        password    : str
            Password to access Splunk daemon.
        dataset     : str
            Dataset type for event log.
        """
        self.username = username
        self.password = password
        self.dataset = dataset

    def delete_log(self, source):
        """Delete a single log file from Splunk.

        Parameters
        ----------
        source  : str
            Identifier for log source. It is usually filename of log.
        """
        # run Python Splunk API command
        source = source.replace(' ', '\ ')
        source = source.split('/')[-1]
        command = 'python /home/hudan/Downloads/splunk-sdk-python-1.6.1/examples/search.py ' + \
                  '--host=192.168.1.106 --port=8089 ' + \
                  '--username=' + self.username + ' --password=' + self.password + \
                  ' "search source=' + self.dataset + '-' + source + \
                  ' host=' + self.dataset + ' sourcetype=linux_secure | delete"'
        os.system(command)

    def bulk_delete(self):
        """Delete all files in the given dataset.
        """
        # get dataset files
        master_path = '/home/hudan/Git/labeled-authlog/dataset/'
        dataset_path = {
            'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
            'SecRepo': master_path + 'SecRepo/auth-perday',
            'forensic-challenge-2010':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-5-2010-perday',
            'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
            'forensic-challenge-2010-syslog':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all'
        }

        # note that in RedHat-based authentication log, parameter '*.log' is not used
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'PySplunk')

        # main process to delete log file and avoid duplicate after re-indexing
        for file_identifier, properties in files.iteritems():
            print file_identifier
            self.delete_log(properties['log_path'])


class Evaluation(object):
    def __init__(self, dataset, log_type):
        self.dataset = dataset
        self.log_type = log_type

    def get_evaluation(self):
        # get dataset files
        master_path = '/home/hudan/Git/labeled-authlog/dataset/'
        dataset_path = {
            'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
            'SecRepo': master_path + 'SecRepo/auth-perday',
            'forensic-challenge-2010':
                master_path + 'Honeynet/forensic-challenge-5-2010/forensic-challenge-5-2010-perday',
            'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
            'Kippo': master_path + 'Kippo/per_day',
            'forensic-challenge-2010-syslog':
                master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all',
            'BlueGene2006': master_path + 'BlueGene2006/per_day',
            'ras': master_path + 'ras/per_day',
            'illustration': master_path + 'illustration/per_day',
            'vpn': master_path + 'vpn/per_day'
        }

        # note that in RedHat-based authentication log, parameter '*.log' is not used
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'PySplunk')

        # open and write result to evaluation file
        fi = open(evaluation_file, 'wt')
        writer = csv.writer(fi)
        writer.writerow(('file_name', 'silhouette', 'dunn'))
        for file_identifier, properties in files.iteritems():
            print file_identifier

            # open pickled clusters
            with open(properties['cluster_pickle'], 'rb') as f:
                clusters = pickle.load(f)

            # open original logs
            with open(properties['log_path'], 'r') as f:
                original_logs = f.readlines()

            mode_csv = 'text-csv'

            # evaluation, get cosine similarity first
            lts = LogTextSimilarity(mode_csv, self.log_type, original_logs, clusters, properties['cosine_path'])
            lts.get_cosine_similarity()

            # get internal evaluation
            si = SilhouetteIndex(mode_csv, clusters, properties['cosine_path'])
            silhoutte_index = si.get_silhouette_index()
            di = DunnIndex(mode_csv, clusters, properties['cosine_path'])
            dunn_index = di.get_dunn_index()

            # write to csv file
            writer.writerow((properties['log_path'].split('/')[-1], silhoutte_index, dunn_index))

            # write to file
            OutputText.txt_percluster(properties['result_percluster'], clusters, mode_csv, None, original_logs)

        fi.close()


if __name__ == '__main__':
    start = time()
    credentials = {
        'username': 'admin',
        'password': '123',
        'output': 'csv'
    }

    syslog_config = {
        'dataset': 'forensic-challenge-2010-syslog',
        'log_type': 'syslog',
        'source_type': 'syslog',
        'evaluation': 'internal'
    }

    kippo_config = {
        'dataset': 'Kippo',
        'log_type': 'kippo',
        'source_type': 'kippo_log',
        'evaluation': 'internal'
    }

    ras_config = {
        'dataset': 'ras',
        'log_type': 'raslog',
        'source_type': 'RAS',
        'evaluation': 'internal'
    }

    auth_config = {
        'dataset': 'Hofstede2014',
        'log_type': 'auth',
        'source_type': 'linux_secure',
        'evaluation': 'internal'
    }

    vpn_config = {
        'dataset': 'vpn',
        'log_type': 'vpnlog',
        'source_type': 'vpn_log',
        'evaluation': 'internal'
    }

    config = kippo_config
    operation_mode = 'evaluation'
    if operation_mode == 'clustering':
        clustering = PySplunk(credentials['username'], credentials['password'], credentials['output'],
                              config['dataset'], config['log_type'], config['source_type'], config['evaluation'])
        clustering.get_bulk_cluster2()
    elif operation_mode == 'upload':
        upload = UploadToSplunk(credentials['username'], credentials['password'], config['dataset'],
                                config['source_type'])
        upload.bulk_upload()
    elif operation_mode == 'delete':
        delete = DeleteFromSplunk(credentials['username'], credentials['password'], config['dataset'])
        delete.bulk_delete()
    elif operation_mode == 'evaluation':
        evaluate = Evaluation(config['dataset'], config['log_type'])
        evaluate.get_evaluation()

    # print runtime
    duration = time() - start
    minute, second = divmod(duration, 60)
    hour, minute = divmod(minute, 60)
    print "Runtime: %d:%02d:%02d" % (hour, minute, second)
