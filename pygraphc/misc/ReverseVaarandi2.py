from os import system
from collections import defaultdict
from numpy import ones
import subprocess


class ReverseVaarandi(object):
    """
    Thanks to Pinjia He for the template processing for SLCT output.
    """
    def __init__(self, mode, support, log_file, outlier_file, output_file):
        self.mode = mode
        self.support = support
        self.log_file = log_file
        self.outlier_file = outlier_file
        self.output_file = output_file
        self.replaced = {'[': '\[', ']': '\]', '/': '\/', '$': '\$', '"': '\"', '*': '\*'}
        self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        self.line_number_file = '/tmp/line_number' + self.log_file.split('/')[-1] + '.txt'
        self.clusters = defaultdict(list)
        self.cluster_index = 0

    def __run_vaarandi(self):
        # run LogCluster or SLCT
        command = ''
        if self.mode == 'LogCluster':
            command = '/home/hudan/Downloads/log-cluster-tool/logcluster-0.08/logcluster.pl --input=' + \
                      self.log_file + ' --support=' + str(self.support) + ' --outliers=' + \
                      self.outlier_file + ' > ' + self.output_file
        elif self.mode == 'SLCT':
            command = '/home/hudan/Desktop/slct-0.05/slct -r -o ' + self.outlier_file + \
                      ' -s ' + str(self.support) + ' ' + self.log_file + ' > ' + self.output_file
        system(command)

    def __parse_outlier(self):
        # parse outlier results
        with open(self.outlier_file, 'r') as fi:
            outliers = fi.readlines()

        outliers_member = []
        for outlier in outliers:
            for k, v in self.replaced.iteritems():
                outlier = outlier.replace(k, v)

            # get outlier line numbers
            cat = subprocess.Popen(('cat', self.log_file), stdout=subprocess.PIPE)
            grep = subprocess.Popen(('grep', '-xn', outlier), stdin=cat.stdout, stdout=subprocess.PIPE)
            with open(self.line_number_file, 'w') as fi:
                cut = subprocess.Popen(('cut', '-f1', '-d:'), stdin=grep.stdout, stdout=fi)
            cat.wait()
            grep.wait()
            cut.wait()

            with open(self.line_number_file, 'r') as fi:
                member_line = fi.readline()
            outliers_member.append(member_line.rstrip())

        # get line number id for outlier clusters
        remove_id = []
        for log_id in outliers_member:
            if log_id != '':
                remove_id.append(int(log_id) - 1)

        return remove_id

    def __parse_abstraction(self):
        # get abstraction per line and cluster member
        with open(self.output_file, 'r') as fi:
            lines = fi.readlines()

        abstractions = {}
        abstraction = ''
        for line in lines:
            if line.startswith('Support:'):
                total_member = int(line.split(': ')[1])
                abstractions[abstraction] = total_member
            elif line == '':
                continue
            else:
                abstraction = line

        return abstractions

    def __match_templog(self, templates, logs, remove_id):
        # match the templates with Logs
        # templates == abstractions
        temp_num = len(templates)
        log_num = len(logs)
        log_label = -1 * ones((log_num, 1))
        for i in range(log_num):
            max_value = -1
            max_index = -1
            if i + 1 in remove_id:
                continue
            for j in range(temp_num):
                lcs = self.__lcs(logs[i], templates[j])
                if lcs >= max_value:
                    max_value = lcs
                    max_index = j
            log_label[i] = max_index

        return log_label

    @staticmethod
    def __lcs(seq1, seq2):
        # calculate the LCS
        lengths = [[0 for _ in range(len(seq2) + 1)] for _ in range(len(seq1) + 1)]

        # row 0 and column 0 are initialized to 0 already
        for i in range(len(seq1)):
            for j in range(len(seq2)):
                if seq1[i] == seq2[j]:
                    lengths[i + 1][j + 1] = lengths[i][j] + 1
                else:
                    lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])

        return lengths[-1][-1]

    def __template_processing(self):
        # read the preprocessed logs
        logs = []
        with open(self.log_file) as lines:
            for line in lines:
                logs.append(line)

        # read the templates
        abstrations = self.__parse_abstraction()
        templates = abstrations.keys()
        temp_num = len(templates)

        # initialize the groups for outlier and templates
        groups = []
        for i in range(temp_num + 1):
            newgroup = []
            groups.append(newgroup)

        # read the outlier and save its id
        remove_id = self.__parse_outlier()
        log_label = self.__match_templog(templates, logs, remove_id)

        for i in range(len(log_label)):
            label = int(log_label[i])
            groups[label + 1].append(i + 1)

        cluster_id = 0
        for numLogOfEachGroup in groups:
            self.clusters[cluster_id] = numLogOfEachGroup
            cluster_id += 1

    def get_cluster(self):
        self.__run_vaarandi()
        self.__template_processing()

        return self.clusters

