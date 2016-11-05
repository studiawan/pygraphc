from nltk import corpus
from collections import Counter
from math import log, pow, sqrt
from re import sub


class PreprocessLog(object):
    """A class to preprocess event log before generating the graph model.
    """
    def __init__(self, logfile=None):
        """Constructor of class PreprocessLog.

        Parameters
        ----------
        logfile : str
            Name of a log file
        """
        self.logfile = logfile
        self.logs = []
        self.loglength = 0
        self.events_list = []
        self.events_unique = []

    def do_preprocess(self):
        """Main method to execute preprocess log.
        """
        # read log file
        self.__read_log()

        # convert to lower, count total logs
        logs_lower = [' '.join(l.lower().split()[5:]) for l in self.logs[:]]
        logs_total = self.loglength

        # preprocess logs, add to ordinary list and unique list
        events_list, events_unique = [], []
        index, index_log = 0, 0
        for l in logs_lower:
            auth_split = l.split()
            event_type, event_desc = auth_split[0].split('[')[0], ' '.join(auth_split[1:])
            event = event_type + ' ' + event_desc
            events_list.append(event)

            preprocessed_event, tfidf = self.get_tfidf(event, logs_total, logs_lower)
            check_events_unique = [e[1]['preprocessed_event'] for e in events_unique]
            # check_events_unique = [e[1]['event'] for e in events_unique]

            # if not exist, add new element
            if preprocessed_event not in check_events_unique:
                # if event not in check_events_unique:
                print index, event
                length = self.get_doclength(tfidf)
                events_unique.append([index, {'event': event, 'tf-idf': tfidf, 'length': length, 'status': '',
                                              'cluster': index, 'frequency': 1, 'member': [index_log],
                                              'preprocessed_event': preprocessed_event}])
                index += 1

            # if exist, increment the frequency
            else:
                for e in events_unique:
                    if preprocessed_event == e[1]['preprocessed_event']:
                        # if event == e[1]['event']:
                        member = e[1]['member']
                        member.append(index_log)
                        e[1]['member'] = member
                        e[1]['frequency'] += 1

            index_log += 1

        # get inter-arrival time of unique event
        timestamps = {}
        for e in events_unique:
            timestamps[e[1]['event']] = [' '.join(l.split()[:3]) for l in self.logs
                                         if e[1]['event'] in ' '.join(l.lower().split())]

        for e in events_unique:
            for k, v in timestamps.iteritems():
                if e[1]['event'] == k:
                    e[1]['start'], e[1]['end'] = v[0], v[-1]

        self.events_list = events_list
        self.events_unique = events_unique

    def __read_log(self):
        """Read a log file.
        """
        with open(self.logfile, 'r') as f:
            logs = f.readlines()

        self.logs = logs
        self.loglength = len(logs)

    @staticmethod
    def __get_wordindocs(word, docs):
        """Find word occurence in all logs. Logs is stated as documents (in the context of information retrieval).

        Parameters
        ----------
        word    : str
            A word in a single event log line.
        docs    : list[str]
            All logs in a file.

        Returns
        -------
        count   : float
            Word occurence in all logs.
        """
        count = 0
        for doc in docs:
            if word in doc:
                count += 1

        count = float(count)
        return count

    def get_tfidf(self, doc, total_docs, docs):
        """Calculate tf-idf (term frequency-inverse document frequency).

        Parameters
        ----------
        doc         : str
            A single event log line.
        total_docs  : float
            Total number of logs or total line numbers.
        docs        : list[str]
            All logs in a file.

        Returns
        -------
        doc         : str
            Preprocessed event logs.
        tfidf       : list[tuple]
            List of tuple where a tuple consists of two elements: 1) word and 2) its tf-idf value.
        """
        # remove number, stopwords
        doc = sub('[^a-zA-Z]', ' ', doc)
        additional_stopwords = ['preauth', 'from', 'xxxxx', 'for', 'port', 'sshd', 'ssh']
        for a in additional_stopwords:
            doc = doc.replace(a, '')
        doc.replace('_', ' ')
        doc = ' '.join(doc.split())

        stopwords = corpus.stopwords.words('english')
        stopwords_result = [w.lower() for w in doc.split() if w.lower() not in stopwords]

        # count word frequency (tf)
        tf = Counter(stopwords_result)
        words_total = len(stopwords_result)
        tfidf = []
        for t in tf.most_common():
            normalized_tf = float(t[1]) / float(words_total)    # normalized word frequency
            wid = self.__get_wordindocs(t[0], docs)             # calculate word occurrence in all documents
            try:
                idf = 1 + log(total_docs / wid)                 # calculate idf
            except ZeroDivisionError:
                idf = 1
            tfidf_val = normalized_tf * idf                     # calculate tf-idf
            tfidf.append((t[0], tfidf_val))

        return doc, tfidf

    @staticmethod
    def get_doclength(tfidf):
        """Calculate doc's length for cosine similarity

        Parameters
        ----------
        tfidf   : list[tuple]
            List of tf-idf value of each word in tuple.
        Returns
        -------
        length  : float
            Document's length.
        """
        length = 0
        for ti in tfidf:
            length += pow(ti[1], 2)

        length = sqrt(length)
        return length
