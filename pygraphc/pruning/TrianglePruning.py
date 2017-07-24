from operator import itemgetter


class TrianglePruning(object):
    """Class for edge pruning based weakest edge weight in each triangle found in the graph.
    """
    def __init__(self, graph):
        """Initialization of class TrianglePruning.

        Parameters
        ----------
        graph   : graph
            Analyzed graph.
        """
        self.graph = graph

    def __remove_edge(self, triangle):
        """Remove the weakest edge in a triangle.

        Parameters
        ----------
        triangle    :
            Tuple of triangle nodes.
        """
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
            self.graph.remove_edge(min_weight[0], min_weight[1])

    def get_triangle(self):
        """Find all triangles in a graph [Schank2005]_. The implementation is a modification
           of [triangleinequality2013]_.

        References
        ----------
        .. [Schank2005] Schank, T., & Wagner, D. Finding, counting and listing all triangles in large graphs,
                        an experimental study. In International Workshop on Experimental and Efficient Algorithms,
                        pp. 606-609, 2005, Springer Berlin Heidelberg.
        .. [triangleinequality2013] Finding Triangles in a Graph.
                                    https://triangleinequality.wordpress.com/2013/09/11/finding-triangles-in-a-graph/

        """
        sorted_degree = sorted(self.graph.degree_iter(), key=itemgetter(1), reverse=True)
        a = {}

        for index, info in enumerate(sorted_degree):
            a[info[0]] = {'ind': index, 'set': set()}

        for first_vertex, degree in sorted_degree:
            for second_vertex in self.graph.neighbors(first_vertex):
                if a[first_vertex]['ind'] < a[second_vertex]['ind']:
                    for third_vertex in a[first_vertex]['set'].intersection(a[second_vertex]['set']):
                        self.__remove_edge((first_vertex, second_vertex, third_vertex))
                    a[second_vertex]['set'].add(first_vertex)
