from itertools import combinations
from datetime import datetime


class ClusterUtility(object):
    """A class contains some utilities to do clustering algorithm.
    """
    @staticmethod
    def get_geometric_mean(weights):
        """Get geometric mean or intensity in a clique. A clique can be a k-clique or maximal clique.

        Parameters
        ----------
        weights : list[float]
            List of edge weight in a clique.

        Returns
        -------
        gmean   : float
            Geometric mean of given edge weights.
        """
        multiplication = 1
        for weight in weights:
            multiplication *= weight

        gmean = 0.0
        if multiplication > 0.0:
            k = float(len(weights))
            gmean = multiplication ** (1 / k)

        gmean = round(gmean, 5)
        return gmean

    @staticmethod
    def get_weighted_cliques(graph, cliques, threshold):
        """Get weighted cliques based on given intensity threshold.

        A clique which its weight are less then threshold is omiited.
        This procedure will filter unsignificant cliques.

        Parameters
        ----------
        graph       : graph
            A graph to check for its weighted cliques.
        cliques     : list[frozenset]
            List of clique list found.
        threshold   : float
            Intensity (geometric mean) threshold.

        Returns
        -------
        weighted_cliques    : list[list]
            List of clique with significant weight.
        """
        weighted_kcliques = []
        for clique in cliques:
            weights = []
            for u, v in combinations(clique, 2):
                reduced_precision = round(graph[u][v][0]['weight'], 5)
                weights.append(reduced_precision)
            gmean = ClusterUtility.get_geometric_mean(weights)

            if gmean > threshold:
                weighted_kcliques.append(frozenset(clique))

        return weighted_kcliques

    @staticmethod
    def set_cluster_id(graph, clusters):
        """Set incremental cluster identifier start from 0.

        Parameters
        ----------
        graph       : graph
            Graph to be set for its cluster id.
        clusters    : dict[list]
            Dictionary contains list of node in a particular cluster.
        """
        for cluster_id, cluster in clusters.iteritems():
            for node in cluster:
                graph.node[node]['cluster'] = cluster_id

    @staticmethod
    def get_cluster_property(graph, clusters, year):
        """Get cluster property.

        Parameters
        ----------
        graph       : graph
            Graph to be analyzed.
        clusters    : dict[list]
            Dictionary contains sequence of nodes in all clusters.
        year        : str
            Year of the log file. We need this parameter since log file does not provide it.

        Returns
        -------
        cluster_property    : dict
            Property of a cluster. For example: frequency of event logs.

        Notes
        -----
        frequency           : frequency of event logs in a cluster.
        member              : number of nodes in a cluster.
        interarrival_rate   : inter-arrival time of event logs timestamp in a cluster.
        """
        cluster_property = {}      # event log frequency per cluster
        for cluster_id, nodes in clusters.iteritems():
            properties = {}
            datetimes = []
            for node_id in nodes:
                properties['frequency'] = properties.get('frequency', 0) + graph.node[node_id]['frequency']
                properties['member'] = properties.get('member', 0) + 1
                datetimes.append(graph.node[node_id]['start'])
                datetimes.append(graph.node[node_id]['end'])

            # get inter-arrival rate
            sorted_datetimes = sorted(datetimes)
            start_temp, end_temp = sorted_datetimes[0].split(), sorted_datetimes[-1].split()  # note that it is -1 not 1
            start = datetime.strptime(' '.join(start_temp[:2]) + ' ' + year + ' ' + ' '.join(start_temp[2:]),
                                      '%b %d %Y %H:%M:%S')
            end = datetime.strptime(' '.join(end_temp[:2]) + ' ' + year + ' ' + ' '.join(end_temp[2:]),
                                    '%b %d %Y %H:%M:%S')
            interarrival_times = end - start
            interarrival = interarrival_times.seconds if interarrival_times.seconds != 0 else 1
            properties['interarrival_rate'] = float(properties['frequency']) / float(interarrival)

            # set cluster property
            cluster_property[cluster_id] = properties

        return cluster_property
