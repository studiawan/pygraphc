import py_stringmatching
from itertools import combinations
from time import time

jw = py_stringmatching.JaroWinkler()
start = time()
log_file = '/home/hs32832011/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/Dec 1.log'
with open(log_file, 'r') as f:
    lines = f.readlines()


log_length = len(lines)
for line1, line2 in combinations(xrange(log_length), 2):
    # string1 = unicode(lines[line1], 'utf-8')
    # string2 = unicode(lines[line2], 'utf-8')
    string1 = lines[line1]
    string2 = lines[line2]
    distance = jw.get_sim_score(string1, string2)
    print distance

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)