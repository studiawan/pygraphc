
class IterativePartitioning(object):
    def __init__(self, logs):
        self.logs = logs
        self.count_partitions = {}
        self.position_partitions = {}

    def __get_token_count(self):
        for log in self.logs:
            tokens = log.strip().split()
            token_count = len(tokens)

            partition_keys = self.count_partitions.keys()
            if token_count not in partition_keys:
                self.count_partitions[token_count] = []
            self.count_partitions[token_count].append(tokens)

    def __get_token_position(self):
        # get total unique token for all columns
        for token_count, partition in self.count_partitions.iteritems():
            if len(partition) > 2:
                token_position = {}
                for partition_index, tokens in enumerate(partition):
                    for column_index, token in enumerate(tokens):
                        if column_index not in token_position.keys():
                            token_position[column_index] = set()
                        token_position[column_index].add(token)

                # get column with minimum count unique token
                min_length = 1
                min_column_index = 0
                for column_index, tokens in token_position.iteritems():
                    token_length = len(token_position[column_index])
                    if token_length < min_length:
                        min_length = token_length
                        min_column_index = column_index

                # split count_partition based on min_column_index found
                new_partition = {}
                for partition_index, tokens in enumerate(partition):
                    for column_index, token in enumerate(tokens):
                        if column_index == min_column_index:
                            if token in token_position[min_column_index]:
                                if token not in new_partition.keys():
                                    new_partition[token] = []
                                new_partition[token].append(tokens)
                print new_partition
            print '---'

    def get_iterative_partitioning(self):
        self.__get_token_count()
        self.__get_token_position()

        return self.position_partitions


log_file = '/home/hudan/Git/labeled-authlog/dataset/vpn/per_day/group1_entrance5.log'
with open(log_file, 'r') as f:
    lines = f.readlines()

ip = IterativePartitioning(lines)
clusters = ip.get_iterative_partitioning()

for tok, cluster in clusters.iteritems():
    for line in cluster:
        print line
    print '---'
