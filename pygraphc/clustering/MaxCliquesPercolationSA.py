from MaxCliquesPercolation import MaxCliquesPercolationWeighted


class MaxCliquesPercolationSA(MaxCliquesPercolationWeighted):
    def __init__(self, graph, edges_weight, nodes_id, k, threshold):
        super(MaxCliquesPercolationSA, self).__init__(graph, edges_weight, nodes_id, k, threshold)

    def get_maxcliques_percolation_sa(self):
        pass
