import csv
from pygraphc.abstraction.ClusterAbstraction import ClusterAbstraction
from pygraphc.clustering.ClusterUtility import ClusterUtility


class AnomalyScore(object):
    """A class to calculate anomaly score in a cluster.
    """
    def __init__(self, graph, clusters, anomaly_path, year):
        """The constructor of class AnomalyScore.

        Parameters
        ----------
        graph       : graph
            A graph to be analyzed for its anomaly.
        clusters    : dict[list]
            Dictionary of list containing node identifier for each clusters.
        anomaly_path    : str
            Filename for anomaly detection result.
        """
        self.graph = graph
        self.clusters = clusters
        self.anomaly_path = anomaly_path
        self.year = year
        # get cluster abstraction and its properties
        self.abstraction = ClusterAbstraction.dp_lcs(self.graph, self.clusters)
        self.property = ClusterUtility.get_cluster_property(self.graph, self.clusters, self.year)
        self.anomaly_score = {}

    def write_property(self):
        """Write cluster property to a file.
        """
        # get anomaly score
        self.get_anomaly_score()

        # write to csv
        f = open(self.anomaly_path, 'wt')
        writer = csv.writer(f)

        # set header
        header = ('cluster_id', 'cluster_abstraction') + tuple(self.property[0].keys()) + ('anomaly_score',)
        writer.writerow(header)

        # write data
        for cluster_id, abstract in self.abstraction.iteritems():
            row = (cluster_id, abstract) + tuple(self.property[cluster_id].values()) + (self.anomaly_score[cluster_id],)
            writer.writerow(row)

        f.close()

    def get_anomaly_score(self):
        """Get anomaly score per cluster.

        Returns
        -------
        anomaly_score   : dict
            Dictionary of anomaly score per cluster.
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
