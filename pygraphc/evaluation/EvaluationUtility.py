
class EvaluationUtility(object):
    @staticmethod
    def convert_to_text(graph, clusters):
        # convert clustering result from graph to text
        new_clusters = {}
        for cluster_id, nodes in clusters.iteritems():
            for node in nodes:
                members = graph.node[node]['member']
                for member in members:
                    new_clusters.setdefault(cluster_id, []).append(member)

        return new_clusters
