import numpy as np
from tables import *
from pygraphc.similarity.StringSimilarity import StringSimilarity


class InternalEvaluation(object):
    """This a class for internal evaluation: validating cluster model without known ground truth.
    """
    @staticmethod
    def __get_node_distance(nodex, neighbors, measurement, mode, graph=None, cosine_similarity=None, h5table=None,
                            h5distance_file=None, events=None, cosine_graph=None):
        """Get distance from a node to its neighbor.

        The neighbors can be located in intra-cluster or inter-cluster. The distance means
        edge weight in the graph case. In non-graph clustering method, node is equal with log line id.

        Parameters
        ----------
        nodex               : int
            Node identifier or log line identifier in incremental integer.
        neighbors           : list
            List of neighbors' node identifier.
        measurement         : str
            Mode of measurement, i.e., min, max, avg.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5table             :
            h5 table which saves cosine similarity result.
        h5distance_file     :
            h5 file for saving distances.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        final_distance  : float
            The average distance of node to its analyzed neighbors.
        """
        h5distance_array = None
        distances = []
        final_distance = 0.
        if mode == 'graph':
            neigbors_weight = graph[nodex]
            for node_id, weight in neigbors_weight.iteritems():
                if node_id in neighbors:
                    distances.append(1 - weight[0]['weight'])

            # if list is empty
            if not distances:
                distances.append(0.)

        elif mode == 'text':
            for neighbor in neighbors:
                if nodex != neighbor:
                    try:
                        distance = cosine_similarity[(nodex, neighbor)]
                    except KeyError:
                        distance = cosine_similarity[(neighbor, nodex)]
                    distances.append(1 - distance)

        elif mode == 'text-h5':
            # create h5 earray
            h5distance_array = h5distance_file.create_earray(h5distance_file.root, 'distance_array', Float32Atom(),
                                                             (0,))
            for neighbor in neighbors:
                if nodex != neighbor:
                    try:
                        dist = [x['similarity'] for x in h5table.iterrows()
                                if x['source'] == nodex and x['dest'] == neighbor]
                        distance = 1 - dist[0]
                    except IndexError:
                        dist = [x['similarity'] for x in h5table.iterrows()
                                if x['source'] == neighbor and x['dest'] == nodex]
                        distance = 1 - dist[0]
                    h5distance_array.append(np.array([distance]))  # append to EArray

            # write h5 distance file
            # h5distance_file.flush()

        elif mode == 'text-cpu':
            total = 0.
            count = 0.
            if measurement == 'min':
                final_distance = 1.
            elif measurement == 'max' or measurement == 'avg':
                final_distance = 0.
            for neighbor in neighbors:
                if nodex != neighbor:
                    try:
                        distance = 1 - StringSimilarity.get_cosine_similarity(events[nodex]['tf-idf'],
                                                                              events[neighbor]['tf-idf'],
                                                                              events[nodex]['length'],
                                                                              events[neighbor]['length'])
                    except KeyError:
                        distance = 1 - StringSimilarity.get_cosine_similarity(events[neighbor]['tf-idf'],
                                                                              events[nodex]['tf-idf'],
                                                                              events[neighbor]['length'],
                                                                              events[nodex]['length'])
                    total += distance
                    count += 1.
                    if measurement == 'min':
                        if distance < final_distance:
                            final_distance = distance
                    elif measurement == 'max':
                        if distance > final_distance:
                            final_distance = distance

            if measurement == 'avg':
                final_distance = total / count

        elif mode == 'text-graph':
            total = 0.
            count = 0.
            if measurement == 'min':
                final_distance = 1.
            elif measurement == 'max' or measurement == 'avg':
                final_distance = 0.
            for neighbor in neighbors:
                if nodex != neighbor:
                    if cosine_graph.has_edge(nodex, neighbor):
                        distance = 1 - cosine_graph[nodex][neighbor][0]['weight']
                    elif cosine_graph.has_edge(neighbor, nodex):
                        distance = 1 - cosine_graph[neighbor][nodex][0]['weight']
                    else:
                        distance = 0.

                    total += distance
                    count += 1.
                    if measurement == 'min':
                        if distance < final_distance:
                            final_distance = distance
                    elif measurement == 'max':
                        if distance > final_distance:
                            final_distance = distance

            if measurement == 'avg':
                final_distance = total / count

        # check for mode
        if mode == 'text' or mode == 'graph':
            if distances:
                if measurement == 'min':
                    final_distance = min(distances)
                elif measurement == 'max':
                    final_distance = max(distances)
                elif measurement == 'avg':
                    final_distance = np.average(distances)
                del distances[:]

        elif mode == 'text-h5':
            if h5distance_array:
                if measurement == 'min':
                    final_distance = np.min(h5distance_file.root.distance_array)
                elif measurement == 'max':
                    final_distance = np.max(h5distance_file.root.distance_array)
                elif measurement == 'avg':
                    final_distance = np.average(h5distance_file.root.distance_array)
                # remove earray
                h5distance_array.remove()

        final_distance = round(final_distance, 3)
        return final_distance

    @staticmethod
    def __get_node_silhoutte(clusters, mode, graph=None, cosine_similarity=None, h5table=None, h5distance_file=None,
                             events=None, cosine_graph=None):
        """Get node silhoutte.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5table             :
            h5 table which saves cosine similarity result.
        h5distance_file     :
            h5 file for saving distances.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        node_silhouttes : dict[int, float]
            A dictionary containing silhoutte per node. Key: node identifier, value: silhoutte.
        """
        cid = set(clusters.keys())
        intracluster_avg, intercluster_avg, node_silhouttes = {}, {}, {}

        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                node_silhouttes[cluster[0]] = 1
            else:
                # get average of intra-cluster distance
                for nodex in cluster:
                    if mode == 'graph':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         graph)
                    elif mode == 'text':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         None, cosine_similarity)
                    elif mode == 'text-h5':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         None, cosine_similarity,
                                                                                         h5table, h5distance_file)
                    elif mode == 'text-cpu':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         None, {}, None, None, events)
                    elif mode == 'text-graph':
                        intracluster_avg[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'avg', mode,
                                                                                         None, {}, None, None, {},
                                                                                         cosine_graph)

                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for nodex in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        if mode == 'graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, graph)
                        elif mode == 'text':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, None, cosine_similarity)
                        elif mode == 'text-h5':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, None, cosine_similarity,
                                                                                   h5table, h5distance_file)
                        elif mode == 'text-cpu':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, None, {}, None, None,
                                                                                   events)
                        elif mode == 'text-graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'avg', mode, None, {}, None, None,
                                                                                   {}, cosine_graph)

                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_avg[nodex] = min(distance.values()) if len(distance.keys()) > 0 else 0.

                # get vertex silhoutte
                for nodex in cluster:
                    try:
                        node_silhouttes[nodex] = (intercluster_avg[nodex] - intracluster_avg[nodex]) / \
                                                 max(intercluster_avg[nodex], intracluster_avg[nodex])
                    except ZeroDivisionError:
                        node_silhouttes[nodex] = 0.

        return node_silhouttes

    @staticmethod
    def __get_cluster_silhoutte(clusters, mode, graph=None, cosine_similarity=None, h5table=None, h5distance_file=None,
                                events=None, cosine_graph=None):
        """Get cluster silhoutte.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5table             :
            h5 table which saves cosine similarity result.
        h5distance_file     :
            h5 file for saving distances.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        cluster_silhouttes  : dict[int, float]
            A dictionary containing silhoutte per cluster. Key: cluster identifier, value: silhoutte.
        """
        node_silhouttes, cluster_silhouttes = {}, {}
        if mode == 'graph':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, graph)
        elif mode == 'text':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, None, cosine_similarity)
        elif mode == 'text-h5':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, None, cosine_similarity, h5table,
                                                                      h5distance_file)
        elif mode == 'text-cpu':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, None, {}, None, None, events)
        elif mode == 'text-graph':
            node_silhouttes = InternalEvaluation.__get_node_silhoutte(clusters, mode, None, {}, None, None, {},
                                                                      cosine_graph)

        for cluster_id, cluster in clusters.iteritems():
            silhoutte = []
            for nodex in cluster:
                silhoutte.append(node_silhouttes[nodex])
            cluster_silhouttes[cluster_id] = np.average(silhoutte) if silhoutte else -1.

        return cluster_silhouttes

    @staticmethod
    def get_silhoutte_index(clusters, mode, graph=None, cosine_similarity=None, h5file='', events=None,
                            cosine_graph=None):
        """Get silhoutte index for a graph [Almeida2011]_.

        Parameters
        ----------
        clusters            : dict[int, list]
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5file              : str
            File name for h5 file which saves cosine similarity result.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        silhoutte_index : float
            The silhoutte index for a graph.

        References
        ----------
        .. [Almeida2011] Helio Almeida, Dorgival Guedes, Wagner Meira Jr, and Mohammed J. Zaki.
                         "Is there a best quality metric for graph clusters?."
                         In Joint European Conference on Machine Learning and Knowledge Discovery in Databases,
                         pp. 44-59. Springer Berlin Heidelberg, 2011.
        """
        cluster_silhouttes = {}
        if mode == 'graph':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, graph)
        elif mode == 'text':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, None, cosine_similarity)
        elif mode == 'text-h5':
            # open h5 file for cosine similarity
            h5cosine_file = open_file(h5file, mode='r')
            h5table = h5cosine_file.root.cosine_group.cosine_table

            # open h5 file for distance
            h5distance_file = open_file('distance.h5', mode='w')

            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, None, cosine_similarity,
                                                                            h5table, h5distance_file)
            h5cosine_file.close()
            h5distance_file.close()
        elif mode == 'text-cpu':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, None, {}, None, None,
                                                                            events)
        elif mode == 'text-graph':
            cluster_silhouttes = InternalEvaluation.__get_cluster_silhoutte(clusters, mode, None, {}, None, None,
                                                                            {}, cosine_graph)

        silhoutte_index = np.average(cluster_silhouttes.values()) if cluster_silhouttes else -1.
        return silhoutte_index

    @staticmethod
    def __get_compactness(clusters, mode, graph=None, cosine_similarity=None, h5file='', h5distance_file=None,
                          events=None, cosine_graph=None):
        """Maximum node distance as diameter to show a compactness of a cluster.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5file              : str
            File name for h5 file which saves cosine similarity result.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        final_compactness   : float
            Diameter or compactness of a cluster.
        """
        compactness = {}
        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                compactness[cluster[0]] = 0.
            else:
                for nodex in cluster:
                    if mode == 'graph':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, graph)
                    elif mode == 'text':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, None,
                                                                                    cosine_similarity)
                    elif mode == 'text-h5':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, None,
                                                                                    cosine_similarity, h5file,
                                                                                    h5distance_file)
                    elif mode == 'text-cpu':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, None,
                                                                                    {}, None, None, events)
                    elif mode == 'text-graph':
                        compactness[nodex] = InternalEvaluation.__get_node_distance(nodex, cluster, 'max', mode, None,
                                                                                    {}, None, None, {}, cosine_graph)
        final_compactness = max(compactness.values()) if compactness else 0.
        return final_compactness

    @staticmethod
    def __get_separation(clusters, mode, graph=None, cosine_similarity=None, h5file='', h5distance_file=None,
                         events=None, cosine_graph=None):
        """Separation or minimum distance between clusters.

        It is actually minimum distance between two nodes in calculated clusters.
        Then, we find the most minimum one for all clusters.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5file              : str
            File name for h5 file which saves cosine similarity result.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        separation  : float
            Minimum distance between all clusters.
        """
        cid = set(clusters.keys())
        intercluster_distance = {}
        separation = 1.
        for cluster_id, cluster in clusters.iteritems():
            # handle cluster with only one node (singleton)
            if len(cluster) == 1:
                if separation <= 1.:
                    pass
            else:
                # all cluster - current cluster, get all nodes in inter cluster
                neighbor_cluster = cid - {cluster_id}
                intercluster_nodes = {}
                for neighbor in neighbor_cluster:
                    intercluster_nodes[neighbor] = clusters[neighbor]

                # get average of inter-cluster distance, and then get its minimal value (closest cluster)
                for nodex in cluster:
                    distance = {}
                    for neighbor in neighbor_cluster:
                        if mode == 'graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, graph)
                        elif mode == 'text':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, None, cosine_similarity)
                        elif mode == 'text-h5':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, None, cosine_similarity,
                                                                                   h5file, h5distance_file)
                        elif mode == 'text-cpu':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, None, {},
                                                                                   None, None, events)
                        elif mode == 'text-graph':
                            temp_distance = InternalEvaluation.__get_node_distance(nodex, intercluster_nodes[neighbor],
                                                                                   'min', mode, None, {},
                                                                                   None, None, {}, cosine_graph)
                        if temp_distance != 0.:
                            distance[neighbor] = temp_distance

                    intercluster_distance[nodex] = min(distance.values()) if len(distance.keys()) > 0 else 1.

                    # get minimum intercluster distance
                    if intercluster_distance[nodex] < separation:
                        separation = intercluster_distance[nodex]

        return separation

    @staticmethod
    def get_dunn_index(clusters, mode, graph=None, cosine_similarity=None, h5file='', events=None, cosine_graph=None):
        """Get Dunn index. The basic formula is separation / compactness [Liu2010]_.

        Parameters
        ----------
        clusters            : dict
            A dictionary containing node identifier per cluster. Key: cluster identifier,
            value: list of node identifier.
        mode                : str
            Mode of clustering method, i.e., graph or text.
        graph               : graph
            A graph to be evaluated.
        cosine_similarity   : dict
            Dictionary of cosine similarity in non-graph clustering. Key: (log_id1, log_id2),
            value: cosine similarity distance.
        h5file              : str
            File name for h5 file which saves cosine similarity result.
        events              : dict
            Dictionary of events with tf-idf and length value.
        cosine_graph        : graph
            Graph of cosine similarity.

        Returns
        -------
        dunn_index  : float
            Dunn index value.

        References
        ----------
        .. [Liu2010] Liu, Y., Li, Z., Xiong, H., Gao, X., & Wu, J. Understanding of internal clustering
                     validation measures. In 2010 IEEE 10th International Conference on Data Mining, pp. 911-916.
        """
        dunn_index = 0.
        if mode == 'graph':
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, graph) / \
                             InternalEvaluation.__get_compactness(clusters, mode, graph)
            except ZeroDivisionError:
                dunn_index = 0.
        elif mode == 'text':
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, None, cosine_similarity) / \
                             InternalEvaluation.__get_compactness(clusters, mode, None, cosine_similarity)
            except ZeroDivisionError:
                dunn_index = 0.

        elif mode == 'text-h5':
            # open h5 file for cosine similarity
            h5cosine_file = open_file(h5file, mode='a')
            h5table = h5cosine_file.root.cosine_group.cosine_table

            # open h5 file for distance
            h5distance_file = open_file('distance.h5', mode='w')
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, None, cosine_similarity, h5table,
                                                                 h5distance_file) / \
                             InternalEvaluation.__get_compactness(clusters, mode, None, cosine_similarity, h5table,
                                                                  h5distance_file)
            except ZeroDivisionError:
                dunn_index = 0.

            # close h5 file
            h5cosine_file.close()
            h5distance_file.close()
        elif mode == 'text-cpu':
            try:
                dunn_index = InternalEvaluation.__get_separation(clusters, mode, None, {}, '', None, events) / \
                             InternalEvaluation.__get_compactness(clusters, mode, None, {}, '', None, events)
            except ZeroDivisionError:
                dunn_index = 0.
        elif mode == 'text-graph':
            try:
                dunn_index = \
                    InternalEvaluation.__get_separation(clusters, mode, None, {}, '', None, {}, cosine_graph) / \
                    InternalEvaluation.__get_compactness(clusters, mode, None, {}, '', None, {}, cosine_graph)
            except ZeroDivisionError:
                dunn_index = 0.

        return dunn_index
