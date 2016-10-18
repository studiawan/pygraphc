
class ClusterAbstraction(object):
    @staticmethod
    def dp_lcs(graph, clusters):
        abstraction = {}
        for cluster_id, nodes in clusters.iteritems():
            data = []
            for node_id in nodes:
                data.append(graph.node[node_id]['preprocessed_event'])
            abstraction[cluster_id] = ClusterAbstraction.lcs(data)

        return abstraction

    @staticmethod
    def lcs(data):
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0]) - i + 1):
                    if j > len(substr) and all(data[0][i:i + j] in x for x in data):
                        substr = data[0][i:i + j]

        return substr
