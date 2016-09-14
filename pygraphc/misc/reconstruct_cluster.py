# a very dirty code to get log lines per cluster from slct and LogCluster output
from re import finditer
from os import system


def get_patterns(output_file):
    with open(output_file, 'r') as f:
        line_patterns = f.readlines()

    patterns = []
    for line_pattern in line_patterns:
        if '*' in line_pattern:
            # get start and end position for each pattern separator such as *{1,1}
            start_pos = []
            end_pos = []
            for position in finditer('{', line_pattern):
                start_pos.append(position.start() - 1)
            for position in finditer('}', line_pattern):
                end_pos.append(position.start() + 1)

            # save separator into a set
            separators = set()
            for index, pos in enumerate(start_pos):
                separators.add(line_pattern[start_pos[index]:end_pos[index]])

            # split log line based on separator found
            split_result = []
            if len(separators) > 1:
                temp = []
                for index, separator in enumerate(separators):
                    if index == 0:
                        temp = line_pattern.strip().split(separator)
                        split_result.append(temp[0])
                    else:
                        res = ''.join(temp[1:]).split(separator)
                        split_result.extend(res)
            else:
                split_result = line_pattern.strip().split(list(separators)[0])

            # check for date < 10
            month_date = split_result[0].split()
            if len(month_date) > 1:
                month, date = month_date[0], month_date[1]
                month_date_new = month + '  ' + date if int(date) < 10 else split_result[0]
                split_result.remove(split_result[0])
                split_result.insert(0, month_date_new)

            patterns.append(split_result)

    return patterns


def get_log_percluster(input_file, patterns, logs):
    # read pattern per cluster, then get log lines per cluster
    clusters = []
    index = 0
    for pattern in patterns:
        percluster_file = 'percluster-' + str(index) + '.cluster'
        index += 1
        grep = ''
        for p in pattern:
            grep += " | grep '" + p + "'"
        command = 'cat ' + input_file + grep + '> ' + percluster_file
        system(command)

        with open(percluster_file, 'r') as f:
            percluster_logs = f.readlines()

        cluster = []
        for log in percluster_logs:
            cluster.append(logs.index(log))

        clusters.append(cluster)

    return clusters


def main():
    input_file = '/home/hudan/Git/labeled-authlog/dataset/161.166.232.21/auth.log.anon'
    output_file = 'output.txt'

    # read input log file
    with open(input_file, 'r') as f:
        logs = f.readlines()

    # run reconstruction
    patterns = get_patterns(output_file)
    clusters = get_log_percluster(input_file, patterns, logs)

    print clusters


main()