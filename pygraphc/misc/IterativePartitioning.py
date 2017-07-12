
class IterativePartitioning(object):
    def __init__(self, logs):
        self.logs = logs
        self.partitions = {}

    def __token_count(self):
        for log in self.logs:
            tokens = log.strip().split()
            token_count = len(tokens)

            partition_keys = self.partitions.keys()
            if token_count in partition_keys:
                self.partitions[token_count].append(log)
            else:
                self.partitions[token_count] = []
                self.partitions[token_count].append(log)

    def __token_position(self):
        for partition in self.partitions:
            print partition
