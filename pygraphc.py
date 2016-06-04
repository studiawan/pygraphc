from optparse import OptionParser
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.KCliquePercolation import KCliquePercolation
from pygraphc.visualization.GraphStreaming import GraphStreaming


def main():
    parser = OptionParser(usage='usage: %prog [options] ')
    parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=['connected_components', 'maxclique_percolation', 'maxclique_percolation_weighted',
                               'kclique_percolation', ],
                      default='kclique_percolation',
                      help='Graph clustering method to run',)
    parser.add_option("-l", "--logfile",
                      action="store",
                      dest="logfile",
                      default="./data/auth.log.anon.nov.1",
                      help="Log file to analyze",)
    parser.add_option("-k", "--kpercolation",
                      action="store",
                      dest="k",
                      default=3,
                      help="Number of k for clique percolation",)
    parser.add_option("-g", "--geometric",
                      action="store",
                      dest="g",
                      default=0.1,
                      help="Threshold of geometric mean for weighted k-clique percolation")
    parser.add_option("-c", "--cosine",
                      action="store",
                      dest="c",
                      default=0.0,
                      help="Threshold for cosine similarity while creating graph edges")

    (options, args) = parser.parse_args()
    logfile = options.logfile
    k = options.k
    geometric_mean = options.g

    # preprocess log file
    p = PreprocessLog(logfile)
    p.do_preprocess()
    events_unique = p.get_eventsunique()

    # create graph
    g = CreateGraph(events_unique, options.c)
    g.do_create()
    graph = g.get_graph()
    edges = g.get_edges_dict()
    edges_weight = g.get_edges_weight()
    nodes_id = g.get_nodes_id()

    # k-clique percolation
    clusters, removed_edges = None, None
    if options.method == 'kclique_percolation':
        kcp = KCliquePercolation(graph, edges_weight, nodes_id, k, geometric_mean)
        kcp.get_kclique_percolation()
        removed_edges = kcp.remove_outcluster()
        clusters = kcp.get_clusters()

    # graph streaming
    stream = GraphStreaming(graph, edges)
    stream.gephi_streaming()
    stream.change_color(clusters)
    stream.remove_outcluster(removed_edges)


if __name__ == '__main__':
    main()