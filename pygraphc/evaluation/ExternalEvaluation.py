from sklearn import metrics
from operator import itemgetter


class ExternalEvaluation(object):
    """A class to evaluate the clustering algorithm.

    At the moment, we deploy all methods implemented in scikit-learn [Pedregosa2011]_.
    The methods are briefly described here [scikit-learn-0.18]_.

    References
    ----------
    .. [Pedregosa2011]     Pedregosa et al., Scikit-learn: Machine Learning in Python, JMLR 12, pp. 2825-2830, 2011.
    .. [scikit-learn-0.18] scikit-learn, Clustering performance evaluation, scikit-learn 0.18 Documentation.
                           http://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation
    """

    @staticmethod
    def set_cluster_label_id(graph, clusters, original_logs, analysis_dir):
        """Get all logs per cluster, get most dominant cluster label, and write clustering result to file [Manning2008]_.

        Parameters
        ----------
        graph           : graph
            Graph to be analyzed.
        clusters        : dict[list]
            Dictionary contains sequence of nodes in all clusters.
        original_logs   :
            List of event logs.
        analysis_dir    : str
            Path to save the analysis result.

        References
        ----------
        .. [Manning2008] Christopher D. Manning, Prabhakar Raghavan & Hinrich Schutze, Evaluation of clustering,
                         in Introduction to Information Retrieval, 2008, Cambridge University Press.
                         http://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-clustering-1.html
        """
        new_cluster_member_label = {}  # store individiual cluster id for each cluster member
        dominant_cluster_labels = {}  # store dominant cluster label from all clusters
        cluster_labels = ['accepted password', 'accepted publickey', 'authentication failure', 'check pass',
                          'connection closed', 'connection reset by peer', 'did not receive identification string',
                          'failed password', 'ignoring max retries', 'invalid user', 'pam adding faulty module',
                          'pam unable to dlopen', 'received disconnect', 'received signal',
                          'reverse mapping checking getaddrinfo', 'server listening', 'session closed',
                          'session opened', 'this does not map back to the address', 'unknown option',
                          'error connect', 'open failed', 'root login refused', 'bad protocol version identification',
                          'subsystem request', 'protocol major versions differ', 'failed none', 'expired password',
                          'unable open env file', 'dispatch protocol error', 'syslogin perform logout',
                          'corrupted mac', 'write ident string']
        max_cluster_id = len(cluster_labels) - 1

        for cluster_id, cluster in clusters.iteritems():
            logs_per_cluster = []
            label_counter = dict((cl, 0) for cl in cluster_labels)
            for c in cluster:
                # get all original_logs per cluster
                # for graph-based clustering
                if graph:
                    members = graph.node[c]['member']
                    for member in members:
                        logs_per_cluster.append(original_logs[member])
                # for non graph-based clustering
                elif graph is None:
                    logs_per_cluster.append(original_logs[c])

                # get dominant label in cluster
                for label in cluster_labels:
                    for log in logs_per_cluster:
                        if label in log.lower():
                            label_counter[label] += 1

            # get most dominant cluster label
            dominant_label_counter = sorted(label_counter.items(), key=itemgetter(1), reverse=True)

            # if cluster label has already used
            if dominant_label_counter[0][0] in [labels[0] for labels in dominant_cluster_labels.values()]:
                # get existing counter
                existing_counter = 0
                existing_label = ''
                for ec in dominant_cluster_labels.values():
                    if ec[0] == dominant_label_counter[0][0]:
                        existing_counter = ec[1]
                        existing_label = ec[0]

                # check for which one is more dominant
                if dominant_label_counter[0][1] > existing_counter:
                    # get existing cluster with lower existing counter
                    existing_cluster = \
                        dominant_cluster_labels.keys()[dominant_cluster_labels.values().index((existing_label,
                                                                                               existing_counter))]
                    for c in cluster:
                        new_cluster_member_label[c] = cluster_labels.index(dominant_label_counter[0][0])
                    # set old cluster to max_cluster_id + 1
                    for c in existing_cluster:
                        new_cluster_member_label[c] = max_cluster_id + 1

                else:
                    for c in cluster:
                        new_cluster_member_label[c] = max_cluster_id + 1
            # if cluster label has not used
            else:
                dominant_cluster_labels[frozenset(cluster)] = dominant_label_counter[0]
                for c in cluster:
                    new_cluster_member_label[c] = cluster_labels.index(dominant_label_counter[0][0])

        analysis_result = {}
        if graph:
            # set new cluster label
            for node_id, new_label in new_cluster_member_label.iteritems():
                graph.node[node_id]['cluster'] = new_label

            # set new cluster id for each cluster member
            for node in graph.nodes_iter(data=True):
                members = node[1]['member']
                for member in members:
                    analysis_result[member] = new_cluster_member_label[node[0]]
        elif graph is None:
            for cluster in clusters:
                for c in cluster:
                    analysis_result[c] = new_cluster_member_label[c]
        # get sorted log line id - cluster id results
        sorted(analysis_result.items(), key=itemgetter(0))

        # write clustering result to file (clustering result for all members in a node)
        fopen = open(analysis_dir, 'w')
        for rowid, cluster_id in analysis_result.iteritems():
            cluster_label = 'undefined' if cluster_id > max_cluster_id else cluster_labels[cluster_id]
            fopen.write(str(cluster_id) + '; ' + cluster_label + '; ' + original_logs[rowid])
        fopen.close()

    @staticmethod
    def get_evaluated(evaluated_file):
        """Get evaluated log file.

        Parameters
        ----------
        evaluated_file  : str
            The evaluated log file.

        Returns
        -------
        evaluation_labels   : list
            Labels for each row in evaluated files.
        """
        with open(evaluated_file, 'r') as ef:
            evaluations = ef.readlines()

        evaluation_labels = [evaluation.split(';')[0] for evaluation in evaluations]
        return evaluation_labels

    @staticmethod
    def get_adjusted_rand(standard_file, prediction_file):
        """Get adjusted rand index [Hubert1985]_.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        adjusted_rand_index : float
            Adjusted rand index.

        References
        ----------
        .. [Hubert1985] Lawrence Hubert and Phipps Arabie. Comparing partitions.
                        Journal of Classification, 2(1):193-218, 1985.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        adjusted_rand_index = metrics.adjusted_rand_score(standard_labels, prediction_labels)

        return adjusted_rand_index

    @staticmethod
    def get_adjusted_mutual_info(standard_file, prediction_file):
        """Get adjusted mutual information (AMI) [Vinh2009]_.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        adjusted_mutual_info    : float
            Adjusted mutual information score.

        References
        ----------
        .. [Vinh2009] Vinh, Nguyen Xuan, Julien Epps, and James Bailey. "Information theoretic measures for
                      clusterings comparison: is a correction for chance necessary?."
                      In Proceedings of the 26th Annual International Conference on Machine Learning,
                      pp. 1073-1080, 2009.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        adjusted_mutual_info = metrics.adjusted_mutual_info_score(standard_labels, prediction_labels)

        return adjusted_mutual_info

    @staticmethod
    def get_normalized_mutual_info(standard_file, prediction_file):
        """Get normalized mutual information (NMI) [Strehl2002]_.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        normalized_mutual_info  : float
            Normalized mutual information score.

        References
        ----------
        .. [Strehl2002] Alexander Strehl and Joydeep Ghosh. Cluster ensembles A knowledge reuse framework
                        for combining multiple partitions. Journal of Machine Learning Research,
                        3(Dec):583-617, 2002.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        normalized_mutual_info = metrics.normalized_mutual_info_score(standard_labels, prediction_labels)

        return normalized_mutual_info

    @staticmethod
    def get_homogeneity_completeness_vmeasure(standard_file, prediction_file):
        """Get homogeneity, completeness, and V-measure score [Rosenberg2007]_.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        homogeneity_completeness_vmeasure   : tuple
            Homogeneity, completeness, and V-measure score

        References
        ----------
        .. [Rosenberg2007] Andrew Rosenberg and Julia Hirschberg. V-Measure: A conditional entropy-based
                           external cluster evaluation measure. In Proceedings of the 2007 Joint Conference on
                           Empirical Methods in Natural Language Processing and Computational
                           Natural Language Learning, volume 7, pages 410-420, 2007.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        homogeneity_completeness_vmeasure = \
            metrics.homogeneity_completeness_v_measure(standard_labels, prediction_labels)

        return homogeneity_completeness_vmeasure

    @staticmethod
    def get_homogeneity(standard_file, prediction_file):
        """Get homogeneity score.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        homogeneity_score   : float
            Homogeneity score.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        homogeneity_score = metrics.homogeneity_score(standard_labels, prediction_labels)

        return homogeneity_score

    @staticmethod
    def get_completeness(standard_file, prediction_file):
        """Get completeness score.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        completeness_score  : float
            Completeness score.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        completeness_score = metrics.completeness_score(standard_labels, prediction_labels)

        return completeness_score

    @staticmethod
    def get_vmeasure(standard_file, prediction_file):
        """Get V-measure score.

        Parameters
        ----------
        standard_file   : str
            The ground truth or standard filename.
        prediction_file : str
            The analyzed or predicted filename.

        Returns
        -------
        vmeasure_score  : float
            V-measure score.
        """
        standard_labels = ExternalEvaluation.get_evaluated(standard_file)
        prediction_labels = ExternalEvaluation.get_evaluated(prediction_file)
        vmeasure_score = metrics.v_measure_score(standard_labels, prediction_labels)

        return vmeasure_score
