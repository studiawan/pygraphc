import jellyfish
import multiprocessing
from itertools import combinations
from time import time


class JaroWinkler(object):
    def __init__(self, logs, log_length):
        self.logs = logs
        self.log_length = log_length

    def __jarowinkler(self, line):
        string1 = unicode(self.logs[line[0]], 'utf-8')
        string2 = unicode(self.logs[line[1]], 'utf-8')
        return jellyfish.jaro_winkler(string1, string2)

    def __call__(self, line):
        return self.__jarowinkler(line)

    def get_jarowinkler(self):
        # get line number combination
        line_combination = list(combinations(xrange(self.log_length), 2))

        # get distance with multiprocessing
        pool = multiprocessing.Pool(processes=4)
        distances = pool.map(self, line_combination)
        pool.close()
        pool.join()

        return distances

# open file
start = time()
log_file = '/home/hs32832011/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/Dec 1.log'
with open(log_file, 'r') as f:
    lines = f.readlines()
log_length = len(lines)

jw = JaroWinkler(lines, log_length)
dist = jw.get_jarowinkler()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
