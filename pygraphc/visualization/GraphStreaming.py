import pygraphc.pygephi
from time import sleep
from random import uniform


class GraphStreaming(object):
    """A class to stream the graph to Gephi.
    """
    def __init__(self, graph_clusters, edges, sleep_time=0):
        """The constructor of class GraphStreaming.

        Parameters
        ----------
        graph_clusters  : graph
            A graph to be visualized in Gephi.
        edges           : dict
            Dictionary of edges. Key: (node1, node2). Value: edge id
        sleep_time      : int
            Time for delaying display in Gephi.
        """
        self.g = graph_clusters
        self.edges = edges
        self.sleep_time = sleep_time
        self.gstream = pygraphc.pygephi.GephiClient('http://localhost:8080/workspace0', autoflush=True)
        self.gstream.clean()

    def change_color(self, colored_object):
        """Change color for a particular object, such as a clique or a cluster.

        Parameters
        ----------
        colored_object  : list
            List of object to be colored.
        """
        # change node color based on objects, e.g., cluster, k-clique, or valid k-cliques
        object_color = self.__set_node_color(colored_object, [])
        for index, objects in enumerate(colored_object):
            node_attributes = {'r': object_color[index][0], 'g': object_color[index][1],
                               'b': object_color[index][2]}
            for node in objects:
                self.gstream.change_node(node, **node_attributes)

            sleep(self.sleep_time)

            # back to normal node size
            node_attributes = {'r': 0.5, 'g': 0.5, 'b': 0.5}
            for node in objects:
                self.gstream.change_node(node, **node_attributes)

    def gephi_streaming(self):
        """Stream the graph to Gephi.
        """
        # streaming nodes
        print 'streaming node ...'
        for node in self.g.nodes_iter(data=True):
            node_attributes = {'size': 10, 'r': 0.5, 'g': 0.5, 'b': 0.5,
                               'preprocessed_event': node[1]['preprocessed_event'],
                               'frequency': node[1]['frequency'], 'cluster': node[1]['cluster']}
            self.gstream.add_node(node[0], **node_attributes)

        # streaming edges
        print 'streaming edge ...'
        edges_only = self.edges.keys()
        for e in edges_only:
            try:
                weight = self.g[e[0]][e[1]]
                edge_index = self.edges[(e[0], e[1])]
            except KeyError:
                weight = self.g[e[1]][e[0]]
                edge_index = self.edges[(e[1], e[0])]

            self.gstream.add_edge(edge_index, e[0], e[1], weight=weight[0]['weight'], directed=False)

    def remove_outcluster(self, removed_edges):
        """Remove edge connecting two nodes in different clusters.

        Parameters
        ----------
        removed_edges   : list[tuple]
            List of tuple containing two connecting nodes.
        """
        # remove edge outside cluster
        for removed_edge in removed_edges:
            try:
                self.gstream.delete_edge(self.edges[(removed_edge[0], removed_edge[1])])
            except KeyError:
                self.gstream.delete_edge(self.edges[(removed_edge[1], removed_edge[0])])

    @staticmethod
    def __set_node_color(colored_object, single_color):
        """Set unique node color per cluster.

        Parameters
        ----------
        colored_object  : iterable
            List of object to be colored.
        single_color    : list
            Flag for single color.

        Returns
        -------
        object_color    : list[tuple]
            List color for each object.
        """
        object_length = len(colored_object)
        object_color = [single_color for _ in range(object_length)] if single_color else \
            [[uniform(0.0, 1.0) for _ in range(3)] for _ in range(object_length)]

        return object_color
