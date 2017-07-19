
class IterativePartitioning(object):
    def __init__(self, logs, subclusters):
        self.logs = logs
        self.subclusters = subclusters
        self.count_partitions = {}
        self.final_partitions = []

    def get_token_count(self):
        # get partition based on token count
        for line_id in self.subclusters:
            tokens = self.logs[line_id].strip().split()
            token_count = len(tokens)

            partition_keys = self.count_partitions.keys()
            if token_count not in partition_keys:
                self.count_partitions[token_count] = []
            self.count_partitions[token_count].append(line_id)

        # convert dictionary to list of list
        self.final_partitions = self.count_partitions.values()

log_file = '/home/hudan/Git/labeled-authlog/dataset/vpn/per_day/group1_entrance5.log'
with open(log_file, 'r') as f:
    lines = f.readlines()

ip = IterativePartitioning(lines, range(20))
ip.get_token_count()

for cluster in ip.final_partitions:
    for line in cluster:
        print lines[line].strip()
    print '---'
