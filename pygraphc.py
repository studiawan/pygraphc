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
                      default=4,
                      help="Number of k for clique percolation",)
    parser.add_option("-t", "--threshold",
                      action="store",
                      dest="t",
                      default=0.10000,
                      help="Threshold of geometric mean for weighted k-clique percolation")

    (options, args) = parser.parse_args()
    logfile = options.logfile
    k = options.k
    t = options.t

    # preprocess log file
    p = PreprocessLog(logfile)
    p.do_preprocess()
    events_unique = p.get_eventsunique()

    # create graph
    g = CreateGraph(events_unique)
    g.do_create()
    graph = g.get_graph()
    edges = g.get_edges_dict()
    edges_weight = g.get_edges_weight()

    # k-clique percolation
    clusters, kcliques, valid_kcliques = None, None, None
    if options.method == 'kclique_percolation':
        kcp = KCliquePercolation(graph, edges_weight, k, t)
        clusters = kcp.get_kclique_percolation()
        kcliques, valid_kcliques = kcp.get_kcliques(), kcp.get_valid_kcliques()

    # graph streaming
    stream = GraphStreaming(graph, edges, clusters, kcliques, valid_kcliques)
    stream.gephi_streaming('valid_kcliques')


if __name__ == '__main__':
    main()