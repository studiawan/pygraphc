import csv


class OutputText(object):
    """OutputText the clustering result to various types of file such as txt, csv, and html.
    """
    @staticmethod
    def txt_perline(perline_file, perline_analysis, max_cluster_id, cluster_labels, original_logs):
        """Write clustering result per line to txt file. This clustering result is for all members in a node.

        Parameters
        ----------
        perline_file            : str
            Filename of output file per line.
        perline_analysis        : dict
            Dictionary of cluster label per log line.
        cluster_labels          : iterable
            List of cluster labels in auth.log.
        max_cluster_id          : int
            Maximum value of cluster identifier.
        original_logs           : iterable
            List of original event logs.
        """
        fopen = open(perline_file, 'w')
        for rowid, cluster_id in perline_analysis.iteritems():
            cluster_label = 'undefined' if cluster_id > max_cluster_id else cluster_labels[cluster_id]
            fopen.write(str(cluster_id) + '; ' + cluster_label + '; ' + original_logs[rowid])
        fopen.close()

    @staticmethod
    def txt_percluster(percluster_file, clusters, mode, graph, original_logs):
        """Write clustering result to txt file.

        Parameters
        ----------
        percluster_file         : str
            Filename of output file per cluster.
        clusters                : dict
            Dictionary of a list containing node identifier per cluster.
        mode                    : str
            Mode of clustering method, i.e., graph or text.
        graph                   : graph
            The graph which its clustering result to be written to a file.
        original_logs           : iterable
            List of original event logs.
        """
        f = open(percluster_file, 'w')
        for cluster_id, nodes in clusters.iteritems():
            f.write('Cluster #' + str(cluster_id) + '\n')
            for node in nodes:
                if mode == 'graph':
                    members = graph.node[node]['member']
                    for member in members:
                        f.write(original_logs[member])
                elif mode == 'text' or mode == 'text-csv':
                    f.write(original_logs[node])
            f.write('\n')

        f.close()

    @staticmethod
    def percluster_with_logid(percluster_file, clusters, original_logs):
        f = open(percluster_file, 'w')
        for cluster_id, log_ids in clusters.iteritems():
            f.write('\nCluster #' + str(cluster_id) + '\n')
            for log_id in log_ids:
                f.write(str(log_id) + ', ' + original_logs[log_id])
        f.close()

    @staticmethod
    def csv_cluster_property(report_file, cluster_property, cluster_abstraction, anomaly_score, quadratic_score,
                             normalized_score, sentiment_score, anomaly_decision, evaluation_metrics):
        """Write cluster property to a csv file.

        Parameters
        ----------
        report_file             : str
            Filename and full path for anomaly score and cluster property.
        cluster_property        : dict
            Dictionary of cluster property.
        cluster_abstraction     : dict
            Dictionary of cluster abstraction.
        anomaly_score           : dict
            Dictionary of anomaly score per cluster.
        quadratic_score         : dict
            Dictionary of quadratic transformation of anomaly score.
        normalized_score        : dict
            Dictionary of normalized anomaly score.
        sentiment_score         : dict
            Dictionary of sentiment score per cluster.
        anomaly_decision        : dict
            Dictionary of anomaly decision per cluster.
        evaluation_metrics      : dict
            Dictionary of all evaluation metrics, both internal and external evaluation.
        """
        # write to csv
        f = open(report_file, 'wt')
        writer = csv.writer(f)

        # set header
        header = ('cluster_id', 'cluster_abstraction') + tuple(cluster_property[0].keys()) + \
                 ('anomaly_score', 'quadratic_score', 'normalized_score', 'sentiment_score', 'final_score', 'decision')
        writer.writerow(header)

        # write data
        for cluster_id, abstract in cluster_abstraction.iteritems():
            row = (cluster_id, abstract) + \
                  tuple(cluster_property[cluster_id].values()) + \
                  (anomaly_score[cluster_id], quadratic_score[cluster_id], normalized_score[cluster_id],
                   sentiment_score[cluster_id]) + anomaly_decision[cluster_id]
            writer.writerow(row)

        # write evaluation metrics
        writer.writerow(('',))
        writer.writerow(('Evaluation metrics of clustering:',))
        for metrics, value in evaluation_metrics.iteritems():
            writer.writerow((metrics, value))

        f.close()

    @staticmethod
    def txt_anomaly_perline(anomaly_decision, clusters, graph, anomaly_perline_file, original_logs):
        """Write anomaly detection result per log line.

        Parameters
        ----------
        anomaly_decision        : dict
            Dictionary of anomaly decision per cluster.
        clusters                : dict
            Dictionary of a list containing node identifier per cluster.
        graph                   : graph
            The graph which its clustering result to be written to a file.
        anomaly_perline_file    : str
            Filename for result of anomaly label per line.
        original_logs           : iterable
            List of original event logs.
        """
        decision_perlog = {}
        for cluster_id, decision in anomaly_decision.iteritems():
            for node in clusters[cluster_id]:
                members = graph.node[node]['member']
                for member in members:
                    decision_perlog[member] = decision

        # write to file
        f = open(anomaly_perline_file, 'w')
        for rowid, decision in decision_perlog.iteritems():
            f.write(decision[1] + '; ' + original_logs[rowid])
        f.close()
