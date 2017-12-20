from os import system
from operator import itemgetter
from collections import defaultdict
import subprocess


class ReverseVaarandi(object):
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
        self.log_id_cluster = defaultdict(list)
        self.cluster_index = 0
        self.big_clusters = defaultdict(list)

    def __run_vaarandi(self):
        # run LogCluster or SLCT
        command = ''
        if self.mode == 'LogCluster':
            command = '/home/hudan/Downloads/log-cluster-tool/logcluster-0.08/logcluster.pl --input=' + \
                      self.log_file + ' --support=' + str(self.support) + ' --outliers=' + \
                      self.outlier_file + ' > ' + self.output_file
        elif self.mode == 'SLCT':
            command = '/home/hudan/Downloads/log-cluster-tool/slct-0.05/slct -r -o ' + self.outlier_file + \
                      ' -s ' + str(self.support) + ' ' + self.log_file + ' > ' + self.output_file
        system(command)
        # print command

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
        for log_id in outliers_member:
            # print log_id
            if log_id != '':
                self.log_id_cluster[int(log_id) - 1].append(self.cluster_index)
                self.clusters[self.cluster_index].append(int(log_id) - 1)

    def __parse_cluster(self):
        # parse clustering result
        # get abstraction per line and cluster member
        with open(self.output_file, 'r') as fi:
            lines = fi.readlines()

        abstractions = []
        line_splits = []
        for line in lines:
            if line.startswith('Support:'):
                # abstraction element: [total_split, total_all_split, total_member, abstraction_list]
                # get all splits of line_splits
                all_splits_length = 0
                for ls in line_splits:
                    all_splits_length += len(ls.split())

                total_member = int(line.split(': ')[1])
                line_splits.insert(0, total_member)
                line_splits.insert(0, all_splits_length)
                line_splits.insert(0, len(line_splits) - 2)
                abstractions.append(line_splits)

            else:
                line = line.rstrip()
                line_splits = line.split('|')
                if line_splits:
                    for line_split in line_splits:
                        for month in self.months:
                            # check day with single digit
                            if line_split.startswith(month):
                                extract_day = line_split.split()
                                day = extract_day[1]
                                if int(day) < 10:
                                    # get day, remove existing, and add new day
                                    day = ' ' + day
                                    extract_day.remove(extract_day[1])
                                    extract_day.insert(1, day)
                                    new_line_split = ' '.join(extract_day)

                                    # get index and add new line split
                                    index = line_splits.index(line_split)
                                    line_splits.remove(line_split)
                                    line_splits.insert(index, new_line_split)
                        # if empty
                        if line_split == '':
                            line_splits.remove(line_split)

        # build big cluster per first pattern found (usually timestamp)
        # abstraction element: [total_split, total_all_split, total_member, abstraction_list]
        for abstraction in abstractions:
            self.big_clusters[abstraction[3]].append(abstraction)

        # sort based on frequency of words
        for key, value in self.big_clusters.iteritems():
            sorted_value = sorted(value, key=itemgetter(1, 0), reverse=True)
            self.big_clusters[key] = sorted_value

    def __compose_run_command(self, value, refine=False):
        commands = list()
        commands.append(['cat', self.log_file])
        for index, abstraction_split in enumerate(value):
            for k, v in self.replaced.iteritems():
                abstraction_split = abstraction_split.replace(k, v)
            if index == 0:
                commands.append(['grep', '-n', abstraction_split])
            elif index > 0 and refine is False:
                commands.append(['grep', abstraction_split])
            elif index > 0 and refine is True:
                commands.append(['grep', '-w', abstraction_split])
        commands.append(['cut', '-f1', '-d:'])

        # run commands
        total_command = len(commands)
        popen_list = []
        for index, command in enumerate(commands):
            if index == 0:
                popen_list.append(subprocess.Popen(command, stdout=subprocess.PIPE))
            elif index == total_command - 1:
                with open(self.line_number_file, 'w') as fi:
                    popen_list.append(
                        subprocess.Popen(command, stdin=popen_list[index - 1].stdout, stdout=fi))
            else:
                popen_list.append(
                    subprocess.Popen(command, stdin=popen_list[index - 1].stdout, stdout=subprocess.PIPE))

            if index > 0:
                popen_list[index - 1].stdout.close()

        # wait for all subprocess finish
        for p in popen_list:
            p.wait()

        return commands

    def __get_cluster_member(self):
        # get cluster member
        with open(self.line_number_file, 'r') as fi:
            member_lines = fi.readlines()
        member_lines = [int(x) - 1 for x in member_lines]

        # save clusters
        for log_id in member_lines:
            # if not in outlier cluster (cluster[0]) and not included in another cluster
            if log_id not in self.clusters[0] and len(self.log_id_cluster[log_id]) == 0:
                self.log_id_cluster[log_id].append(self.cluster_index)
                self.clusters[self.cluster_index].append(int(log_id))

    def get_clusters(self):
        self.__run_vaarandi()
        self.__parse_outlier()
        self.__parse_cluster()
        self.cluster_index += 1

        # get member per cluster
        for key, values in self.big_clusters.iteritems():
            for value in values:
                commands = self.__compose_run_command(value[3:])
                self.__get_cluster_member()

                # check for total members is match or not
                total_member = len(self.clusters[self.cluster_index])
                if value[2] != total_member:
                    print '[WARNING] Total member of a cluster is not match.', value[2], total_member, commands
                    commands = self.__compose_run_command(' '.join(value[3:]).split(), True)
                    self.__get_cluster_member()

                    total_member = len(self.clusters[self.cluster_index])
                    print '[AFTER REFINEMENT]', value[2], total_member, commands

                self.cluster_index += 1

        return self.clusters
