from os import system, remove


class PySplunk(object):
    def __init__(self, username, source, host, output_mode, tmp_file='/tmp/pysplunk_cluster.csv'):
        self.username = username
        self.source = source.replace(' ', '\ ')
        self.host = host
        self.output_mode = output_mode
        self.tmp_file = tmp_file

    def get_splunk_cluster(self):
        # run Python Splunk API command
        command = 'python search.py --username=' + self.username + ' "search source=' + self.source + \
                  ' host=' + self.host + ' sourcetype=linux_secure | cluster labelfield=cluster_id labelonly=t |' \
                                         ' table cluster_id _raw | sort _time | reverse" ' + '--output_mode=' + \
                  self.output_mode + " > " + self.tmp_file
        system(command)

        # get clusters
        with open(self.tmp_file, 'r') as f:
            logs = f.readlines()

        clusters = {}
        for index, log in enumerate(logs):
            cluster_id = log.split(',')[0]
            clusters[cluster_id] = clusters.get(cluster_id, []) + [index]

        # remove tmp_file
        remove(self.tmp_file)

        return clusters
