from nltk import corpus
from collections import Counter
from math import log, pow, sqrt
from re import sub


class PreprocessLog:
    def __init__(self, logfile):
        self.logfile = logfile
        self.logs = []
        self.loglength = 0
        self.events_list = []
        self.events_unique = []

    def do_preprocess(self):
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

            preprocessed_event, tfidf = self.__get_tfidf(event, logs_total, logs_lower)
            check_events_unique = [e[1]['preprocessed_event'] for e in events_unique]

            # if not exist, add new element
            if preprocessed_event not in check_events_unique:
                print index, preprocessed_event
                length = self.__get_doclength(tfidf)
                events_unique.append([index, {'event': event, 'tf-idf': tfidf, 'length': length, 'status': '',
                                              'cluster': 0, 'frequency': 1, 'member': [index_log],
                                              'preprocessed_event':preprocessed_event}])
                index += 1

            # if exist, increment the frequency
            else:
                for e in events_unique:
                    if preprocessed_event == e[1]['preprocessed_event']:
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

    def get_eventslist(self):
        return self.events_list

    def get_eventsunique(self):
        return self.events_unique

    def get_logs(self):
        return self.logs

    def get_loglength(self):
        return self.loglength

    def __read_log(self):
        with open(self.logfile, 'r') as f:
            logs = f.readlines()

        self.logs = logs
        self.loglength = len(logs)

    def __get_wordindocs(self, word, docs):
        # find word occurence in all docs (logs)
        count = 0
        for doc in docs:
            if word in doc:
                count += 1

        return float(count)

    def __get_tfidf(self, doc, total_docs, docs):
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
            wid = self.__get_wordindocs(t[0], docs)               # calculate word occurrence in all documents
            try:
                idf = 1 + log(total_docs / wid)                     # calculate idf
            except ZeroDivisionError:
                idf = 1
            tfidf_val = normalized_tf * idf                     # calculate tf-idf
            tfidf.append((t[0], tfidf_val))

        return doc, tfidf

    def __get_doclength(self, tfidf):
        # calculate doc's length for cosine similarity
        length = 0
        for ti in tfidf:
            length += pow(ti[1], 2)

        return sqrt(length)


