import jellyfish
import multiprocessing
from itertools import combinations


class JaroWinkler(object):
    def __init__(self, event_attributes, event_length):
        self.event_attributes = event_attributes
        self.event_length = event_length

    def __jarowinkler(self, unique_event_id):
        string1 = unicode(self.event_attributes[unique_event_id[0]]['preprocessed_event'], 'utf-8')
        string2 = unicode(self.event_attributes[unique_event_id[1]]['preprocessed_event'], 'utf-8')
        distance = jellyfish.jaro_winkler(string1, string2)
        if distance > 0.:
            return round(distance, 3)

    def __call__(self, unique_event_id):
        distance = self.__jarowinkler(unique_event_id)
        distance_with_id = (unique_event_id[0], unique_event_id[1], distance)
        return distance_with_id

    def get_jarowinkler(self):
        # get unique event id combination
        event_id_combination = list(combinations(xrange(self.event_length), 2))

        # get distance with multiprocessing
        pool = multiprocessing.Pool(processes=4)
        distances = pool.map(self, event_id_combination)
        pool.close()
        pool.join()

        return distances
