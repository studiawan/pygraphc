from sklearn import metrics


class ClusterEvaluation(object):
    @staticmethod
    def get_evaluated(evaluated_file):
        with open(evaluated_file, 'r') as ef:
            evaluations = ef.readlines()

        evaluation_labels = [evaluation.split(';')[0] for evaluation in evaluations]
        return evaluation_labels

    @staticmethod
    def get_adjusted_rand_score(standard_file, prediction_file):
        standard_labels = ClusterEvaluation.get_evaluated(standard_file)
        prediction_labels = ClusterEvaluation.get_evaluated(prediction_file)

        return metrics.adjusted_rand_score(standard_labels, prediction_labels)