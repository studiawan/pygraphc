import networkx as nx
from operator import itemgetter


class TrianglePruning(object):
    def __init__(self, graph):
        self.graph = graph

    def __remove_edge(self, triangle):
        # get weight in triangle
        weight = dict()
        weight[(triangle[0], triangle[1])] = self.graph.get_edge_data(triangle[0], triangle[1])
        weight[(triangle[0], triangle[2])] = self.graph.get_edge_data(triangle[0], triangle[2])
        weight[(triangle[1], triangle[2])] = self.graph.get_edge_data(triangle[1], triangle[2])

        # get minimum weight
        min_weight = (triangle[0], triangle[1], weight[(triangle[0], triangle[1])])
        for nodes, w in weight.iteritems():
            if w < min_weight[2]:
                min_weight = (nodes[0], nodes[1], w)

        # remove edge that has the minimum weight
        if self.graph.has_edge(min_weight[0], min_weight[1]):
            print min_weight[0], min_weight[1]
            self.graph.remove_edge(min_weight[0], min_weight[1])

    def get_triangle(self):
        sorted_degree = sorted(self.graph.degree_iter(), key=itemgetter(1), reverse=True)
        a = {}

        for index, info in enumerate(sorted_degree):
            a[info[0]] = {'ind': index, 'set': set()}

        for first_vertex, degree in sorted_degree:
            for second_vertex in self.graph.neighbors(first_vertex):
                if a[first_vertex]['ind'] < a[second_vertex]['ind']:
                    for third_vertex in a[first_vertex]['set'].intersection(a[second_vertex]['set']):
                        self.__remove_edge((first_vertex, second_vertex, third_vertex))
                        yield (first_vertex, second_vertex, third_vertex)
                    a[second_vertex]['set'].add(first_vertex)


G = nx.Graph()

G.add_edge(1, 2, weight=7)
G.add_edge(1, 3, weight=2)
G.add_edge(1, 4, weight=2)
G.add_edge(1, 5, weight=6)
G.add_edge(2, 3, weight=3)
G.add_edge(4, 5, weight=3)

print G.edges(data=True)
tp = TrianglePruning(G)
for tri in tp.get_triangle():
    print tri
print G.edges(data=True)
