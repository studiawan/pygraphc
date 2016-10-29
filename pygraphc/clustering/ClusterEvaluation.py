from sklearn import metrics


class ClusterEvaluation(object):
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
    def get_adjusted_rand_score(standard_file, prediction_file):
        """Get adjusted rand index.

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
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        adjusted_rand_index = metrics.adjusted_rand_score(standard_labels, prediction_labels)

        return adjusted_rand_index

    @staticmethod
    def get_adjusted_mutual_info_score(standard_file, prediction_file):
        """Get adjusted mutual information (AMI).

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
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        adjusted_mutual_info = metrics.adjusted_mutual_info_score(standard_labels, prediction_labels)

        return adjusted_mutual_info

    @staticmethod
    def get_normalized_mutual_info_score(standard_file, prediction_file):
        """Get normalized mutual information (NMI).

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
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        normalized_mutual_info = metrics.normalized_mutual_info_score(standard_labels, prediction_labels)

        return normalized_mutual_info

    @staticmethod
    def get_homogeneity_completeness_vmeasure(standard_file, prediction_file):
        """Get homogeneity, completeness, and V-measure score.

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
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        homogeneity_completeness_vmeasure = \
            metrics.homogeneity_completeness_v_measure(standard_labels, prediction_labels)

        return homogeneity_completeness_vmeasure


