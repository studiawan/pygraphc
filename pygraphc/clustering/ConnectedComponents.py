import networkx as nx


class ConnectedComponents:
    def __init__(self, g):
        self.g = g

    def get_connected_components(self):
        clusters = []
        for components in nx.connected_components(self.g):
            clusters.append(components)

        cluster_id = 0
        for cluster in clusters:
            for node in cluster:
                self.g[node]['cluster'] = cluster_id
            cluster_id += 1

        return clusters
