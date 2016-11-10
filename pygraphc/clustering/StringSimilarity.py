
class StringSimilarity(object):
    """Class for distance measurement between two vertices.
    """
    @staticmethod
    def get_cosine_similarity(tfidf1, tfidf2, length1, length2):
        """Measure cosine similarity between two strings.

        Typically, it is similarity between two event log messages in the two vertices in
        graph-based event log clustering.

        Parameters
        ----------
        tfidf1  : list
            List of tf-idf measure from the first message.
        tfidf2  : list
            List of tf-idf measure from the second message.
        length1 : float
            Denominator in cosine similarity from the first message.
        length2 : float
            Denominator in cosine similarity from the second message.

        Returns
        -------
        cosine_similarity   : float
            Cosine similarity between two strings.
        """
        vector_products = 0
        for ti1 in tfidf1:
            for ti2 in tfidf2:
                if ti1[0] == ti2[0]:
                    vector_products += ti1[1] * ti2[1]

        try:
            cosine_similarity = vector_products / (length1 * length2)
        except ZeroDivisionError:
            cosine_similarity = 0

        cosine_similarity = round(cosine_similarity, 3)
        return cosine_similarity
