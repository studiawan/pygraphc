from os import system, remove


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
        system(command)

        # get clusters
        with open(self.tmp_file, 'r') as f:
            self.logs = f.readlines()

        clusters = {}
        for index, log in enumerate(self.logs):
            cluster_id = log.split(',')[0]
            clusters[cluster_id] = clusters.get(cluster_id, []) + [index]

        # remove tmp_file
        remove(self.tmp_file)
        return clusters
