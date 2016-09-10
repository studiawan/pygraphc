from optparse import OptionParser
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.ConnectedComponents import ConnectedComponents
from pygraphc.clustering.KCliquePercolation import KCliquePercolation, KCliquePercolationWeighted
from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolation, MaxCliquesPercolationWeighted
from pygraphc.visualization.GraphStreaming import GraphStreaming
from time import time, sleep
from pygraphc.clustering.ClusterUtility import ClusterUtility
from pygraphc.clustering.ClusterEvaluation import ClusterEvaluation


def main():
    standard_path = '/home/hudan/Git/labeled-authlog/dataset/161.166.232.18/'
    standard_file = standard_path + 'auth.log.anon.labeled'
    analyzed_file = standard_path + 'auth.log.anon'

    parser = OptionParser(usage='usage: %prog [options] ')
    parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=['connected_components', 'maxclique_percolation', 'maxclique_percolation_weighted',
                               'kclique_percolation', 'kclique_percolation_weighted'],
                      default='kclique_percolation_weighted',
                      help='Graph clustering method to run',)
    parser.add_option("-l", "--logfile",
                      action="store",
                      dest="logfile",
                      default=analyzed_file,
                      help="Log file to analyze",)
    parser.add_option("-k", "--kpercolation",
                      action="store",
                      dest="k",
                      default=4,
                      help="Number of k for clique percolation",)
    parser.add_option("-g", "--geometric",
                      action="store",
                      dest="g",
                      default=0.5,
                      help="Threshold of geometric mean")
    parser.add_option("-c", "--cosine",
                      action="store",
                      dest="c",
                      default=0.1,
                      help="Threshold for cosine similarity while creating graph edges")

    (options, args) = parser.parse_args()
    logfile = options.logfile
    k = options.k
    geometric_mean_threshold = options.g

    # preprocess log file
    p = PreprocessLog(logfile)
    p.do_preprocess()
    events_unique = p.get_eventsunique()
    logs = p.get_logs()

    # create graph
    g = CreateGraph(events_unique, options.c)
    g.do_create()
    graph = g.get_graph()
    edges = g.get_edges_dict()
    edges_weight = g.get_edges_weight()
    nodes_id = g.get_nodes_id()

    # k-clique percolation
    clusters, removed_edges = None, None
    maxcliques = None

    # prediction result file
    prediction_file = './results-k=' + str(k) + 'g=' + str(geometric_mean_threshold) + '.log'
    # prediction_file = './results-c=' + str(options.c) + '.log'
    if options.method == 'kclique_percolation':
        kcp = KCliquePercolation(graph, edges_weight, nodes_id, k)
        clusters = kcp.get_kclique_percolation()
    elif options.method == 'kclique_percolation_weighted':
        kcpw = KCliquePercolationWeighted(graph, edges_weight, nodes_id, k, geometric_mean_threshold)
        clusters = kcpw.get_kclique_percolation()
        removed_edges = kcpw.get_removed_edges()
    elif options.method == 'connected_components':
        cc = ConnectedComponents(graph)
        clusters = cc.get_clusters()
    elif options.method == 'maxclique_percolation':
        mcp = MaxCliquesPercolation(graph, edges_weight, nodes_id, k)
        clusters = mcp.get_maxcliques_percolation()
    elif options.method == 'maxclique_percolation_weighted':
        mcpw = MaxCliquesPercolationWeighted(graph, edges_weight, nodes_id, k, geometric_mean_threshold)
        clusters = mcpw.get_maxcliques_percolation_weighted()
        maxcliques = mcpw.get_maxcliques()

    # get prediction file
    ClusterUtility.set_cluster_label_id(graph, clusters, logs, prediction_file)

    # graph streaming
    stream_flag = False
    if stream_flag:
        stream = GraphStreaming(graph, edges, 0)
        stream.gephi_streaming()
        # sleep(120)
        # stream.change_color(maxcliques)
        if removed_edges:
            # print 'sleeping for 120 seconds ...'
            # sleep(120)
            stream.remove_outcluster(removed_edges)

    # get evaluation of clustering performance
    adj_rand_score = ClusterEvaluation.get_adjusted_rand_score(standard_file, prediction_file)
    adj_mutual_info_score = ClusterEvaluation.get_adjusted_mutual_info_score(standard_file, prediction_file)
    norm_mutual_info_score = ClusterEvaluation.get_normalized_mutual_info_score(standard_file, prediction_file)
    homogeneity_completeness_vmeasure = ClusterEvaluation.get_homogeneity_completeness_vmeasure(standard_file,
                                                                                                prediction_file)
    return [len(nodes_id), len(edges), len(removed_edges) if removed_edges else 0, len(clusters),
            options.k, options.g, options.c, adj_rand_score, adj_mutual_info_score, norm_mutual_info_score,
            homogeneity_completeness_vmeasure]


if __name__ == '__main__':
    start = time()
    properties = main()
    duration = time() - start
    print 'Nodes         :', properties[0]
    print 'Edges         :', properties[1]
    print 'Removed edges :', properties[2]
    print 'Clusters      :', properties[3]
    print 'k             :', properties[4]
    print 'I             :', properties[5]
    print 'C             :', properties[6]
    print 'Adj rand      :', properties[7]
    print 'Adj mutual    :', properties[8]
    print 'Norm mutual   :', properties[9]
    print 'Hom, comp, v  :', properties[10]
    print 'Runtime       :', duration, 'seconds'