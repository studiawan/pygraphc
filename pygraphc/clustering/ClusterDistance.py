
class ClusterDistance(object):
    @staticmethod
    def get_cosine_similarity(tfidf1, tfidf2, length1, length2):
        vector_products = 0
        for ti1 in tfidf1:
            for ti2 in tfidf2:
                if ti1[0] == ti2[0]:
                    vector_products += ti1[1] * ti2[1]

        try:
            cosine_similarity = vector_products / (length1 * length2)
        except ZeroDivisionError:
            cosine_similarity = 0

        return round(cosine_similarity, 3)
