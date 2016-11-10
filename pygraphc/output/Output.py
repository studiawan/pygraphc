
class Output(object):
    def __init__(self, graph, clusters, original_logs, result_file):
        self.graph = graph
        self.clusters = clusters
        self.original_logs = original_logs
        self.result_file = result_file

    def to_txt(self):
        f = open(self.result_file, 'w')
        for cluster_id, nodes in self.clusters.iteritems():
            f.write('Cluster #' + str(cluster_id) + '\n')
            for node in nodes:
                members = self.graph.node[node]['member']
                for member in members:
                    f.write(self.original_logs[member])
            f.write('\n')

        f.close()
