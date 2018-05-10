from re import sub
from nltk import corpus
import multiprocessing
import datefinder


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
        self.log_grammar = None

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
        line = line.lower()

        # GET month
        matches = datefinder.find_dates(line, source=True)
        months = []
        for match in matches:
            month = sub('[^a-zA-Z]', '', match[1])
            if month:
                months.append(month)

        # only leave alphabet, maintain word split
        line = line.split()
        line_split = []
        for li in line:
            alphabet_only = sub('[^a-zA-Z]', '', li)
            line_split.append(alphabet_only)

        # GET preprocessed_event_countgroup
        preprocessed_event_countgroup = ' '.join(line_split)

        # GET preprocessed_events
        # remove word with length only 1 character
        for index, word in enumerate(line_split):
            if len(word) == 1:
                line_split[index] = ''

        # remove more than one space
        line = ' '.join(line_split)
        line = ' '.join(line.split())

        # remove stopwords
        stopwords = corpus.stopwords.words('english')
        stopwords_month = stopwords
        if months:
            stopwords_month.extend(months)

        stopwords_result = [word for word in line.split() if word not in stopwords_month]
        preprocessed_events = ' '.join(stopwords_result)
        preprocessed_events_graphedge = preprocessed_events

        preprocessed_with_id = (log_index, preprocessed_events, preprocessed_event_countgroup,
                                preprocessed_events_graphedge)
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
        for log_id, event, preprocessed_event_countgroup, preprocessed_events_graphedge in events:
            event_split = event.split()
            if event not in unique_events_only.values():
                unique_events_only[unique_event_id] = event
                self.event_attributes[unique_event_id] = {'preprocessed_event': event_split,
                                                          'preprocessed_event_countgroup':
                                                              preprocessed_event_countgroup.split(),
                                                          'preprocessed_events_graphedge':
                                                              preprocessed_events_graphedge,
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
                attr['preprocessed_events_graphedge'] = attr['preprocessed_event']

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
        for event_id, event in self.count_groups.iteritems():
            # get log id
            original_ids = self.event_attributes[event_id]['member']
            self.events_withduplicates_length = len(original_ids)
            for log_id in original_ids:
                attr = {'preprocessed_event': event, 'log_id': log_id}
                self.event_attributes[log_id] = attr
                self.events_withduplicates.append((log_id, attr))

        return self.events_withduplicates

    @staticmethod
    def refine_preprocessed_event_graphedge(unique_events_subgraph, event_attributes_subgraph, graph):
        # get events for string similarity in graph edge
        unique_events_list = []
        for index, properties in unique_events_subgraph:
            unique_events_list.append(properties['preprocessed_events_graphedge'].split())

        # transpose unique events list
        unique_events_transpose = list(zip(*unique_events_list))

        if len(unique_events_subgraph) > 1:
            # check if each transposed list has the same elements
            true_status = []
            for index, transposed in enumerate(unique_events_transpose):
                status = all(item == transposed[0] for item in transposed)
                if status:
                    true_status.append(index)

            # remove repetitive words
            if true_status:
                true_status = [true_status[0]]
                for index, properties in unique_events_subgraph:
                    graphedge = properties['preprocessed_events_graphedge']
                    refined_graphedge = [y for x, y in enumerate(graphedge.split()) if x not in true_status]
                    properties['preprocessed_events_graphedge'] = ' '.join(refined_graphedge)
                    graph.node[index]['preprocessed_events_graphedge'] = ' '.join(refined_graphedge)

                # remove repetitive words
                for index, properties in event_attributes_subgraph.iteritems():
                    graphedge = properties['preprocessed_events_graphedge']
                    refined_graphedge = [y for x, y in enumerate(graphedge.split()) if x not in true_status]
                    properties['preprocessed_events_graphedge'] = ' '.join(refined_graphedge)

        return unique_events_subgraph, event_attributes_subgraph, graph
