from re import sub
from nltk import corpus
import multiprocessing


class ParallelPreprocess(object):
    def __init__(self, log_file, refine_unique_events=True, count_groups=None):
        self.log_file = log_file
        self.logs = []
        self.log_length = 0
        self.preprocessed_logs = {}
        self.unique_events = []
        self.unique_events_length = 0
        self.event_attributes = {}
        self.refine_unique_events = refine_unique_events
        self.count_groups = count_groups
        self.events_withduplicates = []
        self.events_withduplicates_length = 0

    def __call__(self, line):
        # main method called when running in multiprocessing
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
        line = line.replace('.', '')
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
        # read logs
        self.__read_log()
        logs_with_id = []
        for index, log in enumerate(self.logs):
            logs_with_id.append((index, log))

        # run preprocessing in parallel
        total_cpu = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=total_cpu)
        events = pool.map(self, logs_with_id)
        pool.close()
        pool.join()

        # get graph event_attributes
        unique_events_only = {}
        unique_event_id = 0
        unique_events_list = []
        for log_id, event in events:
            event_split = event.split()
            if event not in unique_events_only.values():
                unique_events_only[unique_event_id] = event
                self.event_attributes[unique_event_id] = {'preprocessed_event': event_split,
                                                          'cluster': unique_event_id,
                                                          'member': [log_id]}
                unique_event_id += 1
                unique_events_list.append(event_split)
            else:
                for index, attr in self.event_attributes.iteritems():
                    if event_split == attr['preprocessed_event']:
                        attr['member'].append(log_id)

            # get preprocessed logs as dictionary
            self.preprocessed_logs[log_id] = event

        # refine unique events to remove repetitive words
        if self.refine_unique_events:
            # transpose unique events list
            unique_events_transpose = map(list, zip(*unique_events_list))

            # check if each transposed list has the same elements
            true_status = []
            for index, transposed in enumerate(unique_events_transpose):
                status = all(item == transposed[0] for item in transposed)
                if status:
                    true_status.append(index)

            # remove repetitive words
            for index, attr in self.event_attributes.iteritems():
                attr['preprocessed_event'] = \
                    [y for x, y in enumerate(attr['preprocessed_event']) if x not in true_status]
                attr['preprocessed_event'] = ' '.join(attr['preprocessed_event'])

        # get unique events for networkx
        self.unique_events_length = unique_event_id
        for index, attr in self.event_attributes.iteritems():
            self.unique_events.append((index, attr))

        return self.unique_events

    def get_unique_events_nopreprocess(self):
        # get unique events without preprocessing. this method is written for event log abstraction.
        unique_event_id = 0
        for event_id, words_split in self.count_groups.iteritems():
            attr = {'preprocessed_event': ' '.join(list(words_split)),
                    'cluster': event_id,
                    'original_id': event_id}
            self.unique_events.append((unique_event_id, attr))
            self.event_attributes[unique_event_id] = attr
            unique_event_id += 1

        self.unique_events_length = len(self.unique_events)
        return self.unique_events

    def get_events_withduplicates(self):
        # get event with duplicates. every log line is a node.
        # read logs
        self.__read_log()
        logs_with_id = []
        index = 0
        for index, log in enumerate(self.logs):
            logs_with_id.append((index, log))
        self.events_withduplicates_length = index + 1

        # run preprocessing in parallel
        total_cpu = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=total_cpu)

        # get events with duplicates
        events = pool.map(self, logs_with_id)
        pool.close()
        pool.join()

        # get graph event_attributes
        for log_id, event in events:
            event_split = event.split()
            attr = {'preprocessed_event': event_split, 'log_id': log_id}
            self.event_attributes[log_id] = attr
            self.events_withduplicates.append((log_id, attr))

            # get preprocessed logs as dictionary
            self.preprocessed_logs[log_id] = event

        return self.events_withduplicates
