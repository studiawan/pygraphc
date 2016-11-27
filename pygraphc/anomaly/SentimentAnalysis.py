from textblob import TextBlob
from operator import itemgetter


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
    def __init__(self, graph, clusters):
        """The constructor of class SentimentAnalysis.

        Parameters
        ----------
        graph       : graph
            The analyzed graph.
        clusters    : dict
            Dictionary of cluster id and its vertices member.
        """
        self.graph = graph
        self.clusters = clusters
        self.cluster_message = {}

    def get_cluster_message(self):
        """Get most frequent message in a cluster.
        """
        for cluster_id, cluster in self.clusters.iteritems():
            event_frequency = {}
            for node in cluster:
                event = self.graph.node[node]['preprocessed_event']
                event_frequency[event] = event_frequency.get(event, 0) + 1
            sorted_event_frequency = sorted(event_frequency.items(), key=itemgetter(1), reverse=True)[0][0]
            self.cluster_message[cluster_id] = sorted_event_frequency

    def get_sentiment(self):
        """Get negative or positive sentiment.

        Default score for sentiment score is -1 to 1. The value that close to 1 means more positive and vice versa.
        The threshold >= 0.

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
