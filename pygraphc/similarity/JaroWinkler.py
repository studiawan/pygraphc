import jellyfish
from itertools import combinations
from time import time

start = time()
log_file = '/home/hs32832011/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/Dec 1.log'
with open(log_file, 'r') as f:
    lines = f.readlines()


log_length = len(lines)
for line1, line2 in combinations(xrange(log_length), 2):
    string1 = unicode(lines[line1], 'utf-8')
    string2 = unicode(lines[line2], 'utf-8')
    distance = jellyfish.jaro_winkler(string1, string2)
    print distance

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)