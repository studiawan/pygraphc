import os
import fnmatch
import csv
from pygraphc.bin.Experiment import get_dataset, get_external_evaluation, get_internal_evaluation


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
                  '--host=192.168.1.106 --port=8089 ' + \
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


if __name__ == '__main__':
    mode = 'upload'
    if mode == 'clustering':
        clustering = PySplunk('admin', '123', 'csv', 'SecRepo', 'auth', 'linux_secure', 'internal')
        clustering.get_bulk_cluster()
    elif mode == 'upload':
        upload = UploadToSplunk('admin', '123', 'SecRepo', 'linux_secure')
        upload.bulk_upload()
    elif mode == 'delete':
        delete = DeleteFromSplunk('admin', '123', 'SecRepo')
        delete.bulk_delete()
