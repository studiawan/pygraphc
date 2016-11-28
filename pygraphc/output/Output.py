import csv
from operator import itemgetter


class Output(object):
    """Output the clustering result to various types of file such as txt, csv, and html.
    """
    def __init__(self, graph, clusters, original_logs, percluster_file,
                 anomaly_score, quadratic_score, normalized_score, cluster_property, cluster_abstraction, report_file,
                 sentiment_score, evaluation_metrics, anomaly_decision):
        """The constructor of class Output.

        Parameters
        ----------
        graph                   : graph
            The graph which its clustering result to be written to a file.
        clusters                : dict[list]
            Dictionary of a list containing node identifier per cluster.
        original_logs           : iterable
            List of original event logs.
        percluster_file         : str
            File name of output file.
        anomaly_score           : dict
            Dictionary of anomaly score per cluster.
        quadratic_score         : dict
            Dictionary of quadratic transformation of anomaly score.
        normalized_score        : dict
            Dictionary of normalized anomaly score.
        cluster_property        : dict
            Dictionary of cluster property.
        cluster_abstraction     : dict
            Dictionary of cluster abstraction.
        report_file             : str
            Filename and full path for anomaly score and cluster property.
        sentiment_score         : dict
            Dictionary of sentiment score per cluster
        evaluation_metrics      : dict
            Dictionary of all evaluation metrics, both internal and external evaluation.
        anomaly_decision        : dict
            Dictionary of anomaly decision per cluster.
        """
        self.graph = graph
        self.clusters = clusters
        self.original_logs = original_logs
        self.percluster_file = percluster_file
        self.anomaly_score = anomaly_score
        self.quadratic_score = quadratic_score
        self.normalized_score = normalized_score
        self.cluster_property = cluster_property
        self.cluster_abstraction = cluster_abstraction
        self.report_file = report_file
        self.sentiment_score = sentiment_score
        self.evaluation_metrics = evaluation_metrics
        self.anomaly_decision = anomaly_decision
        self.anomaly_perline_file = ''

    def txt_percluster(self):
        """Write clustering result to txt file.
        """
        f = open(self.percluster_file, 'w')
        for cluster_id, nodes in self.clusters.iteritems():
            f.write('Cluster #' + str(cluster_id) + '\n')
            for node in nodes:
                members = self.graph.node[node]['member']
                for member in members:
                    f.write(self.original_logs[member])
            f.write('\n')

        f.close()

    def csv_cluster_property(self):
        """Write cluster property to a csv file.
        """
        # write to csv
        f = open(self.report_file, 'wt')
        writer = csv.writer(f)

        # set header
        header = ('cluster_id', 'cluster_abstraction') + tuple(self.cluster_property[0].keys()) + \
                 ('anomaly_score', 'quadratic_score', 'normalized_score', 'sentiment_score', 'final_score', 'decision')
        writer.writerow(header)

        # write data
        for cluster_id, abstract in self.cluster_abstraction.iteritems():
            row = (cluster_id, abstract) + \
                  tuple(self.cluster_property[cluster_id].values()) + \
                  (self.anomaly_score[cluster_id], self.quadratic_score[cluster_id], self.normalized_score[cluster_id],
                   self.sentiment_score[cluster_id]) + self.anomaly_decision[cluster_id]
            writer.writerow(row)

        # write evaluation metrics
        writer.writerow(('',))
        writer.writerow(('Evaluation metrics of clustering:',))
        for metrics, value in self.evaluation_metrics.iteritems():
            writer.writerow((metrics, value))

        f.close()

    def txt_write_anomaly(self):
        """Write anomaly detection result per log line.
        """
        decision_perlog = {}
        for cluster_id, decision in self.anomaly_decision.iteritems():
            for node in self.clusters[cluster_id]:
                members = self.graph.node[node]['member']
                for member in members:
                    decision_perlog[member] = decision
        # sorted(decision_perlog.items(), key=itemgetter(0))

        # write to file
        f = open(self.anomaly_perline_file, 'w')
        for rowid, decision in decision_perlog.iteritems():
            f.write(decision + '; ' + + self.original_logs[rowid])
        f.close()
