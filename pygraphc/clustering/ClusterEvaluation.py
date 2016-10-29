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
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        homogeneity_score = metrics.homogeneity_score(standard_labels, prediction_labels)

        return homogeneity_score

    @staticmethod
    def get_completeness(standard_file, prediction_file):
        """Get completeness score.

        Parameters
        ----------
        standard_file   : str
        prediction_file : str

        Returns
        -------
        completeness_score  : float
            Completeness score.
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        completeness_score = metrics.completeness_score(standard_labels, prediction_labels)

        return completeness_score

    @staticmethod
    def get_vmeasure(standard_file, prediction_file):
        """Get V-measure score.

        Parameters
        ----------
        standard_file   : str
        prediction_file : str

        Returns
        -------
        vmeasure_score  : float
            V-measure score.
        """
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)
        vmeasure_score = metrics.v_measure_score(standard_labels, prediction_labels)

        return vmeasure_score
