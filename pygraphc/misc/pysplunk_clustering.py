import os
import csv
import pickle


class PySplunk(object):
    """Get log clustering using Python Splunk API [SplunkDev2016]_.

    This script is used to cluster log file which manually inputted to Splunk.

    References
    ----------
    .. [SplunkDev2016] Command line examples in the Splunk SDK for Python.
                       http://dev.splunk.com/view/python-sdk/SP-CAAAEFK
    """
    def __init__(self, username, password, output_mode, source, host, log_type, source_type, evaluation,
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
        source          : str
            Source of log file.
        host            : str
            Host of log file.
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
        self.source = source
        self.host = host
        self.log_type = log_type
        self.source_type = source_type
        self.evaluation = evaluation
        self.tmp_file = tmp_file
        self.logs = []
        self.original_logs = []

    def get_splunk_cluster(self):
        """Get log clusters.

        Returns
        -------
        clusters    : dict
            Dictionary of log cluster. Key: cluster_id, value: list of log line identifier.
        """
        # run Python Splunk API command
        command = 'python /home/hudan/Downloads/splunk-sdk-python-1.6.1/examples/search.py ' + \
                  '--host=127.0.0.1 --port=8089 ' + \
                  '--username=' + self.username + ' --password=' + self.password + \
                  ' "search source=' + self.source + \
                  ' host=' + self.host + ' sourcetype=' + self.source_type + \
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

        # get original logs
        for line in self.logs:
            pure_line = line.split(',')[1][1:-2]
            self.original_logs.append(pure_line)

        # get clusters
        clusters = {}
        for index, log in enumerate(self.logs):
            cluster_id = log.split(',')[0]
            clusters[cluster_id] = clusters.get(cluster_id, []) + [index]

        # remove tmp_file
        os.remove(self.tmp_file)
        return clusters

    def get_bulk_cluster(self):
        # open evaluation file
        f = open(self.source + '-clustering.txt', 'wt')
        writer = csv.writer(f)

        # set header
        header = ()
        if self.evaluation == 'internal':
            header = ('file_name', 'silhouette', 'dunn')
        writer.writerow(header)

        # main process to cluster log file
        clusters = self.get_splunk_cluster()

        # write clustering result in dictionary to file
        with open(self.source + '.pickle', 'wb') as f:
            pickle.dump(clusters, f, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    credentials = {
        'username': 'admin',
        'password': '123',
        'output': 'csv'
    }

    syslog_config = {
        'source': 'messages',
        'host': 'app-1',
        'log_type': 'syslog',
        'source_type': 'syslog',
        'evaluation': 'internal'
    }

    kippo_config = {
        'source': '2017-02-14.log',
        'host': 'Kippo-single',
        'log_type': 'kippo',
        'source_type': 'Kippo',
        'evaluation': 'internal'
    }

    ras_config = {
        'source': 'interprid.log',
        'host': 'Interprid',
        'log_type': 'raslog',
        'source_type': 'RAS',
        'evaluation': 'internal'
    }

    auth_config = {
        'source': 'hofstede.log',
        'host': 'Hofstede-single',
        'log_type': 'auth',
        'source_type': 'linux_secure',
        'evaluation': 'internal'
    }

    # change this line to run another dataset
    config = ras_config
    clustering = PySplunk(credentials['username'], credentials['password'], credentials['output'],
                          config['source'], config['host'], config['log_type'], config['source_type'],
                          config['evaluation'])
    clustering.get_bulk_cluster()
