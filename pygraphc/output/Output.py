
class Output(object):
    """Output the clustering result to various types of file such as txt and html.
    """
    def __init__(self, graph, clusters, original_logs, result_file):
        """The constructor of class Output.

        Parameters
        ----------
        graph           : graph
            The graph which its clustering result to be written to a file.
        clusters        : dict[list]
            Dictionary of a list containing node identifier per cluster.
        original_logs   : iterable
            List of original event logs.
        result_file     : str
            File name of output file.
        """
        self.graph = graph
        self.clusters = clusters
        self.original_logs = original_logs
        self.result_file = result_file

    def to_txt(self):
        """Write clustering result to txt file.
        """
        f = open(self.result_file, 'w')
        for cluster_id, nodes in self.clusters.iteritems():
            f.write('Cluster #' + str(cluster_id) + '\n')
            for node in nodes:
                members = self.graph.node[node]['member']
                for member in members:
                    f.write(self.original_logs[member])
            f.write('\n')

        f.close()
