from pygraphc.bin.Experiment import get_dataset
from os import system


class ReverseLogCluster(object):
    def __init__(self, dataset, threshold):
        self.dataset = dataset
        self.threshold = threshold

    def get_cluster(self):
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
        files, evaluation_file = get_dataset(self.dataset, dataset_path[self.dataset], '', '*.log', 'LogCluster')

        # run LogCluster for all files
        clusters = {}
        for f, properties in files.iteritems():
            command = '~/Downloads/log-cluster-tool/logcluster-0.08/logcluster.pl --input=' + properties['log_path'] + \
                      ' --support=' + str(self.threshold) + ' --outliers=' + properties['logcluster_outlier'] + \
                      ' > ' + properties['logcluster_output']
            system(command)

            # parse clustering result
            with open(properties['logcluster_output'], 'r') as fi:
                cluster_abstractions = fi.readlines()

            # replace [ with \[ and ] with \]
            replaced = {'[': '\[', ']': '\]'}
            for index, abstraction in enumerate(cluster_abstractions):
                abstraction_splits = []
                total_member = 0
                if abstraction.startswith('Support:'):
                    total_member = int(abstraction.split()[1])
                else:
                    abstraction_splits = abstraction.split('|')

                # get cluster member
                grep = 'cat ' + properties['log_path'] + ' | '
                for abstraction_split in abstraction_splits:
                    abstraction_split = abstraction_split.strip()
                    if abstraction_split:
                        for key, value in replaced.iteritems():
                            abstraction_split = abstraction_split.replace(key, value)
                        grep += 'grep -n "' + abstraction_split + '" | '
                grep += 'cut -f1 -d: > /tmp/line_number.txt'
                print grep
                system(grep)

                # match total cluster member
                with open('/tmp/line_number.txt', 'r') as fi:
                    member_lines = fi.readlines()

                if total_member != len(member_lines):
                    print 'Total cluster member is NOT match.'

                # save clusters
                clusters[index] = [int(x) - 1 for x in member_lines]

            # save discovered outliers as an independent cluster
            last_index = len(clusters)
            clusters[last_index] = []
            with open(properties['logcluster_outlier'], 'r') as fi:
                outliers = fi.readlines()

            for outlier in outliers:
                for key, value in replaced.iteritems():
                    outlier = outlier.replace(key, value)

                grep = 'grep -n ' + outlier + '| cut -f1 -d: > /tmp/line_number.txt'
                system(grep)
                with open('/tmp/line_number.txt', 'r') as fi:
                    line_number = fi.readline()
                clusters[last_index].append(int(line_number) - 1)

        return clusters

rlc = ReverseLogCluster('forensic-challenge-2010-syslog', 10)
clusterx = rlc.get_cluster()
print clusterx
