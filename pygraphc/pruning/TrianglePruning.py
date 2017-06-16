import networkx as nx
from operator import itemgetter


class TrianglePruning(object):
    def __init__(self, graph):
        self.graph = graph

    def get_triangle(self):
        sorted_degree = sorted(self.graph.degree_iter(), key=itemgetter(1), reverse=True)
        a = {}

        for index, info in enumerate(sorted_degree):
            a[info[0]] = {'ind': index, 'set': set()}

        for first_vertex, degree in sorted_degree:
            for second_vertex in self.graph.neighbors(first_vertex):
                if a[first_vertex]['ind'] < a[second_vertex]['ind']:
                    for third_vertex in a[first_vertex]['set'].intersection(a[second_vertex]['set']):
                        print first_vertex, second_vertex, third_vertex
                    a[second_vertex]['set'].add(first_vertex)


g = nx.complete_graph(5)
tp = TrianglePruning(g)
tp.get_triangle()
