import pygraphc.pygephi
from time import sleep
from random import uniform


class GraphStreaming:
    def __init__(self, graph_clusters, edges, clusters=None, kcliques=None, valid_kcliques=None, sleep_time=0.1):
        self.g = graph_clusters
        self.edges = edges
        self.clusters = clusters
        self.kcliques = kcliques
        self.valid_kcliques = valid_kcliques
        self.sleep_time = sleep_time
        self.objects = {'clusters': self.clusters, 'kcliques': self.kcliques, 'valid_kcliques': self.valid_kcliques}
        self.gstream = pygraphc.pygephi.GephiClient('http://localhost:8080/workspace0', autoflush=True)
        self.gstream.clean()

    def set_node_color(self, colored_object):
        object_length = len(self.objects[colored_object])
        object_color = [[uniform(0.0, 1.0) for _ in range(3)] for _ in range(object_length)]

        return object_color

    def change_color(self, colored_object):
        # change node color based on objects (cluster, k-clique, or valid k-cliques)
        object_color = self.set_node_color(colored_object)
        for index, objects in enumerate(self.objects[colored_object]):
            node_attributes = {'size': 10, 'r': object_color[index][0], 'g': object_color[index][1],
                               'b': object_color[index][2]}
            for node in objects:
                self.gstream.change_node(node, **node_attributes)
                sleep(self.sleep_time)

    def gephi_streaming(self, colored_object):
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

        # change cluster color
        self.change_color(colored_object)

    def remove_outcluster(self, gstream, edge_dict):
        # remove edge outside cluster
        print 'removing unncessary edges ...'
        for node in self.g.nodes_iter(data=True):
            neighbors = self.g.neighbors(node[0])
            for neighbor in neighbors:
                if neighbor != 'cluster':
                    if self.g[node[0]]['cluster'] != self.g[neighbor]['cluster']:
                        try:
                            gstream.delete_edge(edge_dict[(node[0], neighbor)])
                        except KeyError:
                            gstream.delete_edge(edge_dict[(neighbor, node[0])])