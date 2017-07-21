from re import sub
from nltk import corpus
from time import time
import multiprocessing


class ParallelPreprocess(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.log_length = 0

    def __call__(self, line):
        return self.__get_events(line)

    def __read_log(self):
        """Read a log file.
        """
        with open(self.log_file, 'rb') as f:
            self.logs = f.readlines()
        self.log_length = len(self.logs)

    @staticmethod
    def __get_events(line):
        line = sub('[^a-zA-Z]', ' ', line)
        line = line.replace('_', ' ')

        # remove word with length only 1 character
        line_split = line.split()
        for index, word in enumerate(line_split):
            if len(word) == 1:
                line_split[index] = ''

        # remove more than one space
        line = ' '.join(line_split)
        line = ' '.join(line.split())

        # remove stopwords
        stopwords = corpus.stopwords.words('english')
        stopwords_result = [w.lower() for w in line.split() if w.lower() not in stopwords]
        preprocessed_events = ' '.join(stopwords_result)

        return preprocessed_events

    def get_unique_events(self):
        self.__read_log()

        pool = multiprocessing.Pool(processes=4)
        events = pool.map(self, self.logs)
        pool.close()
        pool.join()
        unique_events = set(events)

        return unique_events

# open file
start = time()
logfile = '/home/hudan/Git/labeled-authlog/dataset/SecRepo/auth-perday/dec-2.log'

# preprocess
p = ParallelPreprocess(logfile)
p.get_unique_events()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
