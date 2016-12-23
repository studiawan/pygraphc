import os
import fnmatch


class PySplunk(object):
    """Get log clustering using Python Splunk API [SplunkDev2016]_.

    References
    ----------
    .. [SplunkDev2016] Command line examples in the Splunk SDK for Python.
                       http://dev.splunk.com/view/python-sdk/SP-CAAAEFK
    """
    def __init__(self, username, source, host, output_mode, tmp_file='/tmp/pysplunk_cluster.csv'):
        """The constructor of class PySplunk.

        Parameters
        ----------
        username        : str
            Username to access Splunk daemon. No password required since we use Splunk free version.
        source          : str
            Identifier for log source. It is usually filename of log.
        host            : str
            Hostname for the source log.
        output_mode     : str
            Output for clustering result. Recommended output is csv
        tmp_file        : str
            Path for temporary clustering result.
        """
        self.username = username
        self.source = source.replace(' ', '\ ')
        self.host = host
        self.output_mode = output_mode
        self.tmp_file = tmp_file
        self.logs = []

    def get_splunk_cluster(self):
        """Get log clusters.

        Returns
        -------
        clusters    : dict
            Dictionary of log cluster. Key: cluster_id, value: list of log line identifier.
        """
        # run Python Splunk API command
        command = 'python search.py --username=' + self.username + ' "search source=' + self.source + \
                  ' host=' + self.host + ' sourcetype=linux_secure | cluster labelfield=cluster_id labelonly=t |' \
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


class UploadToSplunk(object):
    def __init__(self, username, password, dataset, sourcetype='linux_secure'):
        self.username = username
        self.password = password
        self.dataset = dataset
        self.sourcetype = sourcetype

    def single_upload(self, log_path):
        log_file = log_path.split('/')[-1]
        command = 'python upload.py --username=' + self.username + ' --password=' + self.password + \
                  ' --sourcetype=' + self.sourcetype + ' --eventhost=' + self.dataset + \
                  ' --source=' + self.dataset + '-' + log_file + ' ' + log_path
        os.system(command)

    def bulk_upload(self):
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

        for match in matches:
            self.single_upload(match)
