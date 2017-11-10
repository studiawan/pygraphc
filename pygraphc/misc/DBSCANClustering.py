from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN


class DBSCANClustering(object):
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.clusters = {}

    def __open_file(self):
        with open(self.log_file, 'r') as f:
            self.logs = f.readlines()

    def get_cluster(self):
        # convert dataset to vector
        vectorizer = TfidfVectorizer(max_df=0.5, max_features=10000, min_df=2, stop_words='english', use_idf=True)
        transformed_data = vectorizer.fit_transform(self.logs)

        # run clustering
        db = DBSCAN(eps=0.7, min_samples=3)
        db.fit(transformed_data)
        print db.labels_

        # get clusters
        for index, label_index in enumerate(db.labels_):
            if label_index not in self.clusters.keys():
                self.clusters[label_index] = []
            self.clusters[label_index].append(index + 1)

        # a single noise as a single new cluster, noise's label is -1 from DBSCAN
        # get the highest cluster index + 1
        continued_index = max(self.clusters.keys()) + 1
        for index in self.clusters[-1]:
            self.clusters[continued_index] = [index]
            continued_index += 1

        return self.clusters
