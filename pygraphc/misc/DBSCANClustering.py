from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from numpy import linspace
from itertools import product
from operator import itemgetter


class DBSCANClustering(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.clusters = {}

    def __open_file(self):
        with open(self.log_file, 'r') as f:
            self.logs = f.readlines()

    def __run_cluster(self, eps, min_samples):
        # convert dataset to vector
        vectorizer = TfidfVectorizer(max_df=0.5, max_features=10000, min_df=2, stop_words='english', use_idf=True)
        transformed_data = vectorizer.fit_transform(self.logs)

        # run clustering
        db = DBSCAN(eps=eps, min_samples=min_samples)
        db.fit(transformed_data)
        print db.labels_

        # get clusters
        clusters = {}
        for index, label_index in enumerate(db.labels_):
            if label_index not in clusters.keys():
                clusters[label_index] = []
            clusters[label_index].append(index + 1)

        # a single noise as a single new cluster, noise's label is -1 from DBSCAN
        # get the highest cluster index + 1
        continued_index = max(clusters.keys()) + 1
        for index in clusters[-1]:
            clusters[continued_index] = [index]
            continued_index += 1

        return clusters

    def get_cluster(self):
        # prepare the parameters
        eps = linspace(0.1, 0.9, 9)
        min_samples = range(1, 6)
        dbscan_parameter = list(product(eps, min_samples))

        # run DBSCAN cluster
        evaluations = {}
        all_clusters = {}
        for parameter in dbscan_parameter:
            clusters = self.__run_cluster(parameter[0], parameter[1])
            all_clusters[parameter] = clusters

            # evaluate clustering result
            # performance = evaluate(clusters)
            # evaluations[(parameter)] = performance

        # get cluster with the best performance
        best_parameter, best_performance = sorted(evaluations.items(), key=itemgetter(1), reverse=True)[0]
        best_cluster = all_clusters[best_parameter]

        return best_cluster
