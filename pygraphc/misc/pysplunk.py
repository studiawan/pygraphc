import os
import fnmatch
import csv
from pygraphc.bin.Experiment import get_dataset, get_evaluation_cluster


class PySplunk(object):
    """Get log clustering using Python Splunk API [SplunkDev2016]_.

    References
    ----------
    .. [SplunkDev2016] Command line examples in the Splunk SDK for Python.
                       http://dev.splunk.com/view/python-sdk/SP-CAAAEFK
    """
    def __init__(self, username, password, output_mode, dataset, tmp_file='/tmp/pysplunk_cluster.csv'):
        """The constructor of class PySplunk.

        Parameters
        ----------
        username        : str
            Username to access Splunk daemon. No password required since we use Splunk free version.
        password        : str
            Password to access Splunk daemon.
        output_mode     : str
            Output for clustering result. Recommended output is csv
        tmp_file        : str
            Path for temporary clustering result.
        """
        self.username = username
        self.password = password
        self.output_mode = output_mode
        self.dataset = dataset
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
                  ' "search source=' + self.dataset + source + \
                  ' host=' + self.dataset + ' sourcetype=linux_secure | cluster labelfield=cluster_id labelonly=t |' \
                                            ' table cluster_id _raw | sort _time | reverse" ' + '--output_mode=' + \
                  self.output_mode + " > " + self.tmp_file
        os.system(command)

        # get clusters
        with open(self.tmp_file, 'r') as f:
            self.logs = f.readlines()

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
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday'
        }

        # note that in RedHat-based authentication log, parameter '*.log' is not used
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'PySplunk')

        # open evaluation file
        f = open(evaluation_file, 'wt')
        writer = csv.writer(f)

        # set header
        header = ('file_name', 'adjusted_rand', 'adjusted_mutual_info', 'normalized_mutual_info',
                  'homogeneity', 'completeness', 'v-measure')
        writer.writerow(header)

        # main process to cluster log file
        for file_identifier, properties in files.iteritems():
            clusters = self.get_splunk_cluster(properties['log_path'])
            original_logs = self.logs
            ar, ami, nmi, h, c, v = get_evaluation_cluster(None, clusters, original_logs, properties)

            # write evaluation result to file
            row = ('/'.join(properties['log_path'].split('/')[-2:]), ar, ami, nmi, h, c, v)
            writer.writerow(row)

        f.close()


class UploadToSplunk(object):
    """Upload log file to Splunk.
    """
    def __init__(self, username, password, dataset, sourcetype='linux_secure'):
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
        log_file = log_path.split('/')[-1]
        log_path = log_path.replace(' ', '\ ')
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
            'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday'
        }

        # get all log files under dataset directory
        matches = []
        # Debian-based: /var/log/auth.log
        if self.dataset == 'Hofstede2014' or self.dataset == 'SecRepo' or self.dataset == 'forensic-challenge-2010':
            for root, dirnames, filenames in os.walk(dataset_path[self.dataset]):
                for filename in fnmatch.filter(filenames, '*.log'):
                    matches.append(os.path.join(root, filename))
        # RedHat-based: /var/log/secure
        elif self.dataset == 'hnet-hon-2004' or self.dataset == 'hnet-hon-2006':
            file_lists = os.listdir(dataset_path[self.dataset])
            matches = [dataset_path[self.dataset] + '/' + filename
                       for filename in file_lists if not filename.endswith('.labeled')]

        # upload to Splunk
        for match in matches:
            self.single_upload(match)

if __name__ == '__main__':
    clustering = PySplunk('admin', '123', 'csv', 'hnet-hon-2004')
    clustering.get_bulk_cluster()
