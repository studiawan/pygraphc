from os import system
from operator import itemgetter
import subprocess


class ReverseVaarandi(object):
    def __init__(self, mode, support, log_file, outlier_file, output_file):
        self.mode = mode
        self.support = support
        self.log_file = log_file
        self.outlier_file = outlier_file
        self.output_file = output_file

    def get_clusters(self):
        # initialization
        replaced = {'[': '\[', ']': '\]', '/': '\/', '$': '\$', '"': '\"', '*': '\*'}
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        clusters = {}
        cluster_index = 0

        # run LogCluster or SLCT
        command = ''
        if self.mode == 'LogCluster':
            command = '~/Downloads/log-cluster-tool/logcluster-0.08/logcluster.pl --input=' + self.log_file + \
                      ' --support=' + str(self.support) + ' --outliers=' + self.outlier_file + ' > ' + self.output_file
        elif self.mode == 'SLCT':
            command = '~/Downloads/log-cluster-tool/slct-0.05/slct -r -o ' + self.outlier_file + \
                      ' -s ' + str(self.support) + ' ' + self.log_file
        system(command)

        # parse outlier results
        with open(self.outlier_file, 'r') as fi:
            outliers = fi.readlines()

        outliers_member = []
        for outlier in outliers:
            for k, v in replaced.iteritems():
                outlier = outlier.replace(k, v)

            # get outlier line numbers
            cat = subprocess.Popen(('cat', self.log_file), stdout=subprocess.PIPE)
            grep = subprocess.Popen(('grep', '-xn', outlier), stdin=cat.stdout, stdout=subprocess.PIPE)
            with open('/tmp/line_number.txt', 'w') as fi:
                cut = subprocess.Popen(('cut', '-f1', '-d:'), stdin=grep.stdout, stdout=fi)
            cat.wait()
            grep.wait()
            cut.wait()

            with open('/tmp/line_number.txt', 'r') as fi:
                member_line = fi.readline()
            outliers_member.append(member_line.rstrip())

        # get line number id for outlier clusters
        clusters[cluster_index] = [int(x) - 1 for x in outliers_member]
        cluster_index += 1

        # parse clustering result
        # get abstraction per line and cluster member
        with open(self.output_file, 'r') as fi:
            lines = fi.readlines()

        abstractions = []
        for line in lines:
            if line.startswith('Support:'):
                # abstraction element: [total_split, total_member, abstraction_list]
                total_member = int(line.split(': ')[1])
                # line_splits = []      # do not add this line
                line_splits.insert(0, total_member)
                line_splits.insert(0, len(line_splits) - 1)
                abstractions.append(line_splits)

            else:
                line = line.rstrip()
                line_splits = line.split('|')
                if line_splits:
                    for line_split in line_splits:
                        for month in months:
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
        # abstraction element: [total_split, total_member, abstraction_list]
        big_clusters = {}
        for abstraction in abstractions:
            if abstraction[2] not in big_clusters.keys():
                big_clusters[abstraction[2]] = []
                big_clusters[abstraction[2]].append(abstraction)
            else:
                big_clusters[abstraction[2]].append(abstraction)

        # sort based on frequency
        for key, value in big_clusters.iteritems():
            sorted_value = sorted(value, key=itemgetter(0), reverse=True)
            big_clusters[key] = sorted_value

        # get member per cluster
        for key, values in big_clusters.iteritems():
            for value in values:
                commands = list()
                commands.append(['cat', self.log_file])
                for index, abstraction_split in enumerate(value[2:]):
                    for k, v in replaced.iteritems():
                        abstraction_split = abstraction_split.replace(k, v)
                    if index == 0:
                        commands.append(['grep', '-n', abstraction_split])
                    else:
                        commands.append(['grep', abstraction_split])
                commands.append(['cut', '-f1', '-d:'])

                # run commands
                total_command = len(commands)
                popen_list = []
                for index, command in enumerate(commands):
                    if index == 0:
                        popen_list.append(subprocess.Popen(command, stdout=subprocess.PIPE))
                    elif index == total_command - 1:
                        with open('/tmp/line_number.txt', 'w') as fi:
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

                # get cluster member
                with open('/tmp/line_number.txt', 'r') as fi:
                    member_lines = fi.readlines()
                member_lines = [int(x) - 1 for x in member_lines]
                total_member = len(member_lines)

                # check for members in other clusters
                if value[1] != total_member:
                    for index, cluster in clusters.iteritems():
                        member_lines = list(set(member_lines) - set(cluster))
                    total_member = len(member_lines)
                    if value[1] != total_member:
                        print 'After evaluation', value[1], total_member, commands

                # save clusters
                clusters[cluster_index] = member_lines
                cluster_index += 1

        return clusters
