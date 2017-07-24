from collections import Counter
from math import log, sqrt


class CosineSimilarity(object):
    def __init__(self, string1, string2):
        self.string1 = string1
        self.string2 = string2
        self.docs = [self.string1, self.string2]
        self.total_docs = len(self.docs)
        self.word_count = {}

    def __get_word_in_docs(self, word):
        # if word exist in dictionary
        count = 0
        if word in self.word_count.keys():
            count = self.word_count[word]
        else:
            for doc in self.docs:
                if word in doc:
                    count += 1
            self.word_count[word] = count
        count = float(count)

        return count

    def __get_tfidf(self, string):
        string_split = string.split()
        tf = Counter(string_split)                      # calculate tf
        total_words = len(string_split)
        tfidf = []
        for t in tf.most_common():
            normalized_tf = float(t[1]) / float(total_words)
            wid = self.__get_word_in_docs(t[0])
            idf = 1 + log(self.total_docs / wid)    # calculate idf
            tfidf_val = normalized_tf * idf             # calculate tf-idf
            tfidf.append((t[0], tfidf_val))

        return tfidf

    @staticmethod
    def __get_doclength(tfidf):
        length = 0
        for ti in tfidf:
            length += pow(ti[1], 2)

        length = sqrt(length)
        return length

    def get_cosine_similarity(self):
        tfidf1 = self.__get_tfidf(self.string1)
        tfidf2 = self.__get_tfidf(self.string2)
        vector_products = 0
        for ti1 in tfidf1:
            for ti2 in tfidf2:
                if ti1[0] == ti2[0]:
                    vector_products += ti1[1] * ti2[1]

        length1 = self.__get_doclength(tfidf1)
        length2 = self.__get_doclength(tfidf2)
        try:
            cosine_similarity = vector_products / (length1 * length2)
        except ZeroDivisionError:
            cosine_similarity = 0

        cosine_similarity = round(cosine_similarity, 3)
        return cosine_similarity


str1 = 'invalid user test'
str2 = 'invalid user admin'
cs = CosineSimilarity(str1, str2)
similarity = cs.get_cosine_similarity()
print similarity
