
class ClusterAbstraction(object):
    """Get cluster abstraction based on longest common substring [jtjacques2010]_.

    References
    ----------
    .. [jtjacques2010] jtjacques, Longest common substring from more than two strings - Python.
       http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python.
    """
    @staticmethod
    def dp_lcs(graph, clusters):
        """The processed string are preprocessed message from raw event log messages.

        Parameters
        ----------
        graph       : graph
            A graph to be processed.
        clusters    : dict[list]
            Dictionary containing a list of node identifier per cluster.
        Returns
        -------
        abstraction : dict[str]
            Dictionary of abstraction string per cluster.
        """
        abstraction = {}
        for cluster_id, nodes in clusters.iteritems():
            data = []
            for node_id in nodes:
                data.append(graph.node[node_id]['preprocessed_event'])
            abstraction[cluster_id] = ClusterAbstraction.lcs(data)

        return abstraction

    @staticmethod
    def lcs(data):
        """Get longest common substring from multiple string.

        Parameters
        ----------
        data    : list[str]
            List of string to be processed.
        Returns
        -------
        substr  : str
            A single string as longest common substring.
        """
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0]) - i + 1):
                    if j > len(substr) and all(data[0][i:i + j] in x for x in data):
                        substr = data[0][i:i + j]

        return substr
