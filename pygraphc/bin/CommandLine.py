#!/usr/bin/env python

from optparse import OptionParser
from time import time
from pygraphc.anomaly.AnomalyScore import AnomalyScore
from pygraphc.anomaly.SentimentAnalysis import SentimentAnalysis
from pygraphc.clustering.ConnectedComponents import ConnectedComponents
from pygraphc.clustering.GraphEntropy import GraphEntropy
from pygraphc.clustering.KCliquePercolation import KCliquePercolation, KCliquePercolationWeighted
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolation, MaxCliquesPercolationWeighted
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.visualization.GraphStreaming import GraphStreaming
from pygraphc.output.OutputText import OutputText


def run():
    """This is the main function to run pygraphc in one line command.

    Notes
    -----
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
    silhoutte_index     : float
        Silhoutte index for internal evaluation of clustering.
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
                      default='improved_majorclust',
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
    parser.add_option('-t', '--ground-truth-file',
                      action='store',
                      dest='t',
                      # /home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/Dec 25.log.labeled
                      default='',
                      help='A ground truth for analyzed log file.')
    parser.add_option('-f', '--analyzed-file',
                      action='store',
                      dest='f',
                      # /home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday/Dec 25.log
                      default='',
                      help='A log file to be analyzed.')
    parser.add_option('-o', '--output-txt',
                      action='store',
                      dest='o',
                      # /home/hudan/Git/pygraphc/result/misc/Dec 25.log.percluster
                      default='',
                      help='OutputText of clustering result in text file per cluster.')
    parser.add_option('-a', '--anomaly-file',
                      action='store',
                      dest='a',
                      # /home/hudan/Git/pygraphc/result/misc/Dec 25.log.anomaly.csv
                      default='',
                      help='OutputText of anomaly detection in csv file.')
    parser.add_option('-l', '--anomaly-ground-truth',
                      action='store',
                      dest='l',
                      # /home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_attack/Dec 25.log.attack
                      default='',
                      help='Ground truth of anomaly detection file.')
    parser.add_option('-n', '--anomaly-perline-file',
                      action='store',
                      dest='n',
                      # /home/hudan/Git/pygraphc/result/misc/Dec 25.log.anomaly.perline.txt
                      default='',
                      help='OutputText of anomaly detection in txt file per log line.')
    parser.add_option('-p', '--prediction-file',
                      action='store',
                      dest='p',
                      # /home/hudan/Git/pygraphc/result/misc/Dec 25.log.perline
                      default='',
                      help='OutputText of clustering result in txt file per line.')
    parser.add_option('-y', '--year',
                      action='store',
                      dest='y',
                      default='2014',
                      help='Year in log file. In some log files, this data is not available.')

    # get options
    (options, args) = parser.parse_args()
    k = options.k
    geometric_mean_threshold = options.g

    groundtruth_file = options.t
    analyzed_file = options.f
    percluster_file = options.o
    anomaly_file = options.a
    prediction_file = options.p
    anomaly_perline_file = options.n
    anomaly_groundtruth = options.l
    year = options.y

    # preprocess log file
    p = PreprocessLog(analyzed_file)
    p.do_preprocess()
    events_unique = p.events_unique
    logs = p.logs

    # variable initialization
    graph, clusters, removed_edges = None, None, None
    score, quadratic_score, normalized_score, cluster_property, cluster_abstraction = {}, {}, {}, {}, {}
    sentiment_score, anomaly_decision = {}, {}

    if options.method in graph_method:
        # create graph
        g = CreateGraph(events_unique, options.c)
        g.do_create()
        graph = g.g
        edges = g.edges_dict
        edges_weight = g.edges_weight
        edges_dict = g.edges_dict
        nodes_id = g.get_nodes_id()

        # run the selected method
        if options.method == 'kclique_percolation':
            kcp = KCliquePercolation(graph, edges_weight, nodes_id)
            kcp.init_kclique_percolation(k)
            clusters = kcp.get_kclique_percolation(k)
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'kclique_percolation_weighted':
            kcpw = KCliquePercolationWeighted(graph, edges_weight, nodes_id)
            kcpw.init_kclique_percolation(k)
            clusters = kcpw.get_kclique_percolation_weighted(k, geometric_mean_threshold)
            removed_edges = kcpw.removed_edges
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'connected_components':
            cc = ConnectedComponents(graph)
            clusters = cc.get_clusters()
            if options.s:
                graph_streaming(graph, edges, None)
        elif options.method == 'maxclique_percolation':
            mcp = MaxCliquesPercolation(graph, edges_weight, nodes_id)
            mcp.init_maxclique_percolation()
            clusters = mcp.get_maxcliques_percolation(k)
            if options.s:
                graph_streaming(graph, edges, removed_edges)
        elif options.method == 'maxclique_percolation_weighted':
            mcpw = MaxCliquesPercolationWeighted(graph, edges_weight, nodes_id)
            mcpw.init_maxclique_percolation()
            clusters = mcpw.get_maxcliques_percolation_weighted(k, geometric_mean_threshold)
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

        # check for evaluation
        if groundtruth_file and anomaly_file and anomaly_groundtruth:
            # get prediction file
            ExternalEvaluation.set_cluster_label_id(graph, clusters, logs, prediction_file, 'auth')

            # get sentiment analysis
            sentiment = SentimentAnalysis(graph, clusters)
            sentiment.get_cluster_message()
            sentiment_score = sentiment.get_sentiment()

            # get anomaly score and the decision
            anomaly = AnomalyScore(graph, clusters, year, edges_dict, sentiment_score, 'auth')
            anomaly.get_anomaly_score()
            anomaly.get_anomaly_decision()

            # get anomaly-related value
            score = anomaly.anomaly_score
            cluster_property = anomaly.property
            cluster_abstraction = anomaly.abstraction
            quadratic_score = anomaly.quadratic_score
            normalized_score = anomaly.normalization_score
            anomaly_decision = anomaly.anomaly_decision

    elif options.method in nongraph_method:
        pass

    # check for evaluation
    if groundtruth_file and anomaly_file and anomaly_groundtruth:
        # get external evaluation of clustering performance
        adj_rand_score = ExternalEvaluation.get_adjusted_rand(groundtruth_file, prediction_file)
        adj_mutual_info_score = ExternalEvaluation.get_adjusted_mutual_info(groundtruth_file, prediction_file)
        norm_mutual_info_score = ExternalEvaluation.get_normalized_mutual_info(groundtruth_file, prediction_file)
        homogeneity = ExternalEvaluation.get_homogeneity(groundtruth_file, prediction_file)
        completeness = ExternalEvaluation.get_completeness(groundtruth_file, prediction_file)
        vmeasure = ExternalEvaluation.get_vmeasure(groundtruth_file, prediction_file)

        # get internal evaluation
        silhoutte_index = InternalEvaluation.get_silhoutte_index(graph, clusters)

        # get external evaluation of anomaly detection performance
        anomaly_adj_rand_score = ExternalEvaluation.get_adjusted_rand(anomaly_groundtruth, anomaly_perline_file)
        anomaly_adj_mutual_info_score = ExternalEvaluation.get_adjusted_mutual_info(anomaly_groundtruth,
                                                                                    anomaly_perline_file)
        anomaly_norm_mutual_info_score = ExternalEvaluation.get_normalized_mutual_info(anomaly_groundtruth,
                                                                                       anomaly_perline_file)
        anomaly_homogeneity = ExternalEvaluation.get_homogeneity(anomaly_groundtruth, anomaly_perline_file)
        anomaly_completeness = ExternalEvaluation.get_completeness(anomaly_groundtruth, anomaly_perline_file)
        anomaly_vmeasure = ExternalEvaluation.get_vmeasure(anomaly_groundtruth, anomaly_perline_file)

        # arrange dictionary of evaluation metrics
        evaluation_metrics = {
            'adj_rand_score': adj_rand_score, 'adj_mutual_info_score': adj_mutual_info_score,
            'norm_mutual_info_score': norm_mutual_info_score,
            'homogeneity': homogeneity, 'completeness': completeness, 'vmeasure': vmeasure,
            'silhoutte_index': silhoutte_index,
            'anomaly_adj_rand_score': anomaly_adj_rand_score,
            'anomaly_adj_mutual_info_score': anomaly_adj_mutual_info_score,
            'anomaly_norm_mutual_info_score': anomaly_norm_mutual_info_score,
            'anomaly_homogeneity': anomaly_homogeneity,
            'anomaly_completeness': anomaly_completeness, 'anomaly_vmeasure': anomaly_vmeasure
        }

        OutputText.csv_cluster_property(anomaly_file, cluster_property, cluster_abstraction, score, quadratic_score,
                                        normalized_score, sentiment_score, anomaly_decision, evaluation_metrics)

    # get output per cluster, cluster property, and anomaly score
    OutputText.txt_percluster(percluster_file, clusters, graph, logs)
    OutputText.txt_anomaly_perline(anomaly_decision, clusters, graph, anomaly_perline_file, logs)


def graph_streaming(graph, edges, removed_edges):
    stream = GraphStreaming(graph, edges, 0)
    stream.gephi_streaming()
    if removed_edges:
        stream.remove_outcluster(removed_edges)

if __name__ == '__main__':
    start = time()
    run()
    duration = time() - start
    print 'Runtime       :', duration, 'seconds'
