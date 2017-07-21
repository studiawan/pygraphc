from re import sub
from nltk import corpus
import multiprocessing


class ParallelPreprocess(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.log_length = 0
        self.unique_events = []
        self.unique_events_length = 0
        self.event_attributes = {}

    def __call__(self, line):
        return self.__get_events(line)

    def __read_log(self):
        """Read a log file.
        """
        with open(self.log_file, 'rb') as f:
            self.logs = f.readlines()
        self.log_length = len(self.logs)

    @staticmethod
    def __get_events(logs_with_id):
        log_index, line = logs_with_id
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
        preprocessed_with_id = (log_index, preprocessed_events)

        return preprocessed_with_id

    def get_unique_events(self):
        self.__read_log()
        logs_with_id = []
        for index, log in enumerate(self.logs):
            logs_with_id.append((index, log))

        pool = multiprocessing.Pool(processes=4)
        events = pool.map(self, logs_with_id)
        pool.close()
        pool.join()

        # get graph event_attributes
        unique_events_only = {}
        unique_event_id = 0
        for log_id, event in events:
            if event not in unique_events_only.values():
                unique_events_only[unique_event_id] = event
                self.event_attributes[unique_event_id] = {'preprocessed_event': event,
                                                          'cluster': unique_event_id,
                                                          'member': [log_id]}
                unique_event_id += 1
            else:
                for index, attr in self.event_attributes.iteritems():
                    if event == attr['preprocessed_event']:
                        attr['member'].append(log_id)

        # get unique events for networkx
        self.unique_events_length = unique_event_id
        for index, attr in self.event_attributes.iteritems():
            self.unique_events.append((index, attr))

        return self.unique_events
