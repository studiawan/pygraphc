from textblob import TextBlob


class SentimentAnalysis(object):
    """Get sentiment analysis with only positive and negative considered.

    Positive means normal logs and negative sentiment refers to possible attacks.
    This class uses sentiment analysis feature from the TextBlob library [Loria2016]_.

    References
    ----------
    .. [Loria2016] Steven Loria and the contributors, TextBlob: Simple, Pythonic, text processing--Sentiment analysis,
                   part-of-speech tagging, noun phrase extraction, translation, and more.
                   https://github.com/sloria/TextBlob/
    """
    def __init__(self, cluster_message):
        self.cluster_message = cluster_message

    def get_sentiment(self):
        """Get negative or positive sentiment.

        Default score for sentiment score is -1 to 1. The value that close to 1 means more positive and vice versa.

        Returns
        -------
        sentiment_score : dict
            A dictionary containing key: cluster id and value: sentiment score.
        """
        sentiment_score = {}
        for cluster_id, message in self.cluster_message.iteritems():
            possible_sentiment = TextBlob(message)
            if possible_sentiment.sentiment.polarity >= 0.:
                sentiment_score[cluster_id] = possible_sentiment.sentiment.polarity
            elif possible_sentiment.sentiment.polarity < 0.:
                sentiment_score[cluster_id] = possible_sentiment.sentiment.polarity

        return sentiment_score

    def get_normalized_sentiment(self):
        """Get normalized sentiment score.

        Returns
        -------
        normalized_score    : dict
            A dictionary containing key: cluster id and value: normalized sentiment score.
        """
        sentiment_score = self.get_sentiment()
        normalized_score = {}
        min_score = min(sentiment_score.values())
        max_score = max(sentiment_score.values())
        for cluster_id, score in sentiment_score.iteritems():
            normalized_score[cluster_id] = (score - min_score) / (max_score - min_score)

        return normalized_score
