from optparse import OptionParser
from time import time  # , sleep

from pygraphc.anomaly.AnomalyScore import AnomalyScore
from pygraphc.clustering.ClusterUtility import ClusterUtility
from pygraphc.clustering.ConnectedComponents import ConnectedComponents
from pygraphc.clustering.GraphEntropy import GraphEntropy
from pygraphc.clustering.KCliquePercolation import KCliquePercolation, KCliquePercolationWeighted
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolation, MaxCliquesPercolationWeighted
from pygraphc.evaluation.ClusterEvaluation import ClusterEvaluation
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.visualization.GraphStreaming import GraphStreaming


def main():
    """This is the main function to run pygraphc in one line command.

    Returns
    -------
    len(nodes_id)       : int
        Number of nodes in the analyzed graph.
    len(edges)          : int
        Number of edges in the processed graph.
    len(removed_edges)  : int
        Number of removed edges after clustering.
    len(clusters)       : int
        Number of generated clusters.
    options.k           : int
        Number of percolation (intersection) in k-clique or maximal clique method.
    options.g           : float
        Threshold of geometric mean.
    options.c           : float
        Threshold for cosine similarity while creating edges.
    adj_rand_score      : float
        Adjusted rand index.
    adj_mutual_info_score               : float
        Adjusted mutual information.
    norm_mutual_info_score              : float
        Normalized mutual information.
    homogeneity_completeness_vmeasure   : float
        Homogeneity, completeness and V-measure.
    """
    graph_method = ['connected_components', 'maxclique_percolation', 'maxclique_percolation_weighted',
                    'kclique_percolation', 'kclique_percolation_weighted', 'majorclust', 'improved_majorclust',
                    'graph_entropy']
    nongraph_method = ['iplom', 'lke']
    methods = graph_method + nongraph_method

    parser = OptionParser(usage='usage: %prog [options] ')
    parser.add_option('-m', '--method',
                      type='choice',
                      action='store',
                      dest='method',
                      choices=methods,
                      default='graph_entropy',
                      help='Graph clustering method to run.')
    parser.add_option('-k', '--kpercolation',
                      action='store',
                      dest='k',
                      default=3,
                      help='Number of k for clique percolation.')
    parser.add_option('-g', '--geometric',
                      action='store',
                      dest='g',
                      default=0.1,
                      help='Threshold of geometric mean.')
    parser.add_option('-c', '--cosine',
                      action='store',
                      dest='c',
                      default=0.0,
                      help='Threshold for cosine similarity while creating edges.')
    parser.add_option('-s', '--stream',
                      action='store',
                      dest='s',
                      default=False,
                      help='Streaming the processed graph to Gephi.')
    parser.add_option('-d', '--ground-truth-dir',
                      action='store',
                      dest='d',
                      default='/home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1/161.166.232.17/',
                      help='A path for ground truth directory.')
    parser.add_option('-t', '--ground-truth-file',
                      action='store',
                      dest='t',
                      default='dec-7.log.labeled',
                      help='A ground truth for analyzed log file.')
    parser.add_option('-f', '--analyzed-file',
                      action='store',
                      dest='f',
                      default='dec-7.log',
                      help='A log file to be analyzed.')

    # get options
    (options, args) = parser.parse_args()
    k = options.k
    geometric_mean_threshold = options.g

    groundtruth_path = options.d
    groundtruth_file = groundtruth_path + options.t
    analyzed_file = groundtruth_path + options.f

    # preprocess log file
    p = PreprocessLog(analyzed_file)
    p.do_preprocess()
    events_unique = p.get_eventsunique()
    logs = p.get_logs()

    # variable initialization for return value
    prediction_file = ''
    nodes_id = []
    edges = {}
    clusters, removed_edges = None, None

    if options.method in graph_method:
        # create graph
        g = CreateGraph(events_unique, options.c)
        g.do_create()
        graph = g.get_graph()
        edges = g.get_edges_dict()
        edges_weight = g.get_edges_weight()
        nodes_id = g.get_nodes_id()

        # prediction result file
        if options.method in ['maxclique_percolation', 'maxclique_percolation_weighted', 'kclique_percolation',
                              'kclique_percolation_weighted']:
            prediction_file = './results-k=' + str(k) + '-g=' + str(geometric_mean_threshold) + \
                              '-c=' + str(options.c) + '.log'
        elif options.method in ['connected_components']:
            prediction_file = './results-c=' + str(options.c) + '.log'
        elif options.method in ['majorclust', 'improved_majorclust', 'graph_entropy']:
            prediction_file = './results.log'

        # run the selected method
        if options.method == 'kclique_percolation':
            kcp = KCliquePercolation(graph, edges_weight, nodes_id, k)
            clusters = kcp.get_kclique_percolation()
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'kclique_percolation_weighted':
            kcpw = KCliquePercolationWeighted(graph, edges_weight, nodes_id, k, geometric_mean_threshold)
            clusters = kcpw.get_kclique_percolation()
            removed_edges = kcpw.get_removed_edges()
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'connected_components':
            cc = ConnectedComponents(graph)
            clusters = cc.get_clusters()
            if options.s:
                graph_streaming(graph, edges, None)
        elif options.method == 'maxclique_percolation':
            mcp = MaxCliquesPercolation(graph, edges_weight, nodes_id, k)
            clusters = mcp.get_maxcliques_percolation()
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'maxclique_percolation_weighted':
            mcpw = MaxCliquesPercolationWeighted(graph, edges_weight, nodes_id, k, geometric_mean_threshold)
            clusters = mcpw.get_maxcliques_percolation_weighted()
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'majorclust':
            # please note that this method is not suitable for a dense graph.
            mc = MajorClust(graph)
            clusters = mc.get_majorclust(graph)
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'improved_majorclust':
            imc = ImprovedMajorClust(graph)
            clusters = imc.get_improved_majorclust()
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'graph_entropy':
            ge = GraphEntropy(graph)
            clusters = ge.get_graph_entropy()
            if options.s:
                graph_streaming(graph, edges, removed_edges)

        # get prediction file
        ClusterUtility.set_cluster_label_id(graph, clusters, logs, prediction_file)

        # get anomaly score
        anomaly_score = AnomalyScore(graph, clusters, '')
        anomaly_score.write_property()

    elif options.method in nongraph_method:
        pass

    # get evaluation of clustering performance
    adj_rand_score = ClusterEvaluation.get_adjusted_rand_score(groundtruth_file, prediction_file)
    adj_mutual_info_score = ClusterEvaluation.get_adjusted_mutual_info_score(groundtruth_file, prediction_file)
    norm_mutual_info_score = ClusterEvaluation.get_normalized_mutual_info_score(groundtruth_file, prediction_file)
    homogeneity_completeness_vmeasure = ClusterEvaluation.get_homogeneity_completeness_vmeasure(groundtruth_file,
                                                                                                prediction_file)
    return [len(nodes_id), len(edges), len(removed_edges) if removed_edges else 0, len(clusters),
            options.k, options.g, options.c, adj_rand_score, adj_mutual_info_score, norm_mutual_info_score,
            homogeneity_completeness_vmeasure]


def graph_streaming(graph, edges, removed_edges):
    stream = GraphStreaming(graph, edges, 0)
    stream.gephi_streaming()
    if removed_edges:
        # print 'sleeping for 120 seconds ...'
        # sleep(120)
        stream.remove_outcluster(removed_edges)

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
