from pygraphc.abstraction.ClusterAbstraction import ClusterAbstraction
from pygraphc.clustering.ClusterUtility import ClusterUtility


class AnomalyScore(object):
    """A class to calculate anomaly score in a cluster.
    """
    def __init__(self, graph, clusters, year, edges_dict, sentiment_score, logtype):
        """The constructor of class AnomalyScore.

        Parameters
        ----------
        graph           : graph
            A graph to be analyzed for its anomaly.
        clusters        : dict[list]
            Dictionary of list containing node identifier for each clusters.
        year            : str
            Year of event logs.
        edges_dict      : dict
            Dictionary of edges in the analyzed graph. Key: (node1, node2), value: index.
        sentiment_score : dict
            Dictionary of sentiment score per cluster.
        logtype         : str
            Type of event log, i.e., auth, kippo.
        """
        self.graph = graph
        self.clusters = clusters
        self.year = year
        self.edges_dict = edges_dict
        self.sentiment_score = sentiment_score
        self.logtype = logtype

        self.anomaly_score = {}
        self.quadratic_score = {}
        self.normalization_score = {}
        self.anomaly_decision = {}

        # get cluster abstraction and its properties
        self.abstraction = ClusterAbstraction.dp_lcs(self.graph, self.clusters)
        self.property = ClusterUtility.get_cluster_property(self.graph, self.clusters, self.year,
                                                            self.edges_dict, self.logtype)

    def get_anomaly_score(self):
        """Get anomaly score per cluster.
        """
        total_nodes = 0
        total_frequency = 0

        # get total nodes and total frequency
        for cluster_id, properties in self.property.iteritems():
            total_nodes += properties['member']
            total_frequency += properties['frequency']

        # calculate anomaly score
        for cluster_id, properties in self.property.iteritems():
            self.anomaly_score[cluster_id] = float(properties['member'] * properties['frequency']) / \
                                        float(total_nodes * total_frequency) * properties['interarrival_rate']
        # normalized anomaly score
        self.__transform_score()

    def __transform_score(self):
        """Transform anomaly score to quadratic score.

        This model will generate:
        - Low intensity attack  : low score
        - High intensity attack : low score
        - Normal                : high score.
        """
        # the anomaly score need to be normalized first
        # first normalization: from 0 to 1
        first_normalization = {}
        min_score = min(self.anomaly_score.values())
        max_score = max(self.anomaly_score.values())
        for cluster_id, score in self.anomaly_score.iteritems():
            try:
                first_normalization[cluster_id] = (score - min_score) / (max_score - min_score)
            except ZeroDivisionError:
                first_normalization[cluster_id] = 0

        # quadratic score to have a more appropriate anomaly score
        for cluster_id, score in first_normalization.iteritems():
            self.quadratic_score[cluster_id] = -4 * (score ** 2) + (4 * score)

        # second normalization: from -1 to 1 to have a threshold in 0
        min_score = min(self.quadratic_score.values())
        max_score = max(self.quadratic_score.values())
        a, b = -1, 1
        for cluster_id, score in self.quadratic_score.iteritems():
            try:
                self.normalization_score[cluster_id] = a + ((score - min_score) * (b - a)) / (max_score - min_score)
            except ZeroDivisionError:
                self.normalization_score[cluster_id] = 0.

    def get_anomaly_decision(self, sentiment=True):
        """Get decision whether an event log is anomaly or normal.

        Parameters
        ----------
        sentiment   : bool
            True if using sentiment analysis and false means the method only considering
            normalization score (anomaly score).
        """
        for cluster_id, anomaly_score in self.normalization_score.iteritems():
            final_score = (anomaly_score + self.sentiment_score[cluster_id]) / 2 if sentiment else anomaly_score
            self.anomaly_decision[cluster_id] = (final_score, 'attack') if final_score < 0 else (final_score, 'normal')
