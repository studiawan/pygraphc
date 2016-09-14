# a very dirty code to get log lines per cluster from slct and LogCluster output

import re


def splitter(string, delimiter):
    return string.split(delimiter)

output_file = 'output.txt'
with open(output_file, 'r') as f:
    line_patterns = f.readlines()

for line_pattern in line_patterns:
    if '*' in line_pattern:
        separators = set()
        print line_pattern.strip()
        start_pos = []
        end_pos = []
        for position in re.finditer('{', line_pattern):
            start_pos.append(position.start() - 1)
        for position in re.finditer('}', line_pattern):
            end_pos.append(position.start() + 1)

        for index, pos in enumerate(start_pos):
            separators.add(line_pattern[start_pos[index]:end_pos[index]])

        split_result = []
        if len(separators) > 1:
            temp = []
            for index, separator in enumerate(separators):
                if index == 0:
                    temp = splitter(line_pattern.strip(), separator)
                    split_result.append(temp[0])

                else:
                    res = splitter(''.join(temp[1:]), separator)
                    split_result.extend(res)

        else:
            split_result = line_pattern.strip().split(list(separators)[0])

        print 'result', split_result
        print '-------------'