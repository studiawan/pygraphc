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
    def __init__(self, log_message):
        self.log_message = log_message

    def get_sentiment(self):
        """Get negative or positive sentiment.

        Returns
        -------
        sentiment_score : tuple
            A tuple containing (sentiment, polarity score).
        """
        possible_sentiment = TextBlob(self.log_message)
        sentiment_score = None
        if possible_sentiment.sentiment.polarity >= 0.:
            sentiment_score = ('positive', possible_sentiment.sentiment.polarity)
        elif possible_sentiment.sentiment.polarity < 0.:
            sentiment_score = ('negative', possible_sentiment.sentiment.polarity)

        return sentiment_score
