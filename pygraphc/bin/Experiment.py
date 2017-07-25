import fnmatch
import os
import csv
import networkx as nx
from time import time
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.clustering.GraphEntropy import GraphEntropy
from pygraphc.clustering.MaxCliquesPercolation import MaxCliquesPercolationWeighted
from pygraphc.clustering.MaxCliquesPercolationSA import MaxCliquesPercolationSA
from pygraphc.misc.IPLoM import ParaIPLoM, IPLoM
from pygraphc.misc.LKE import Para, LKE
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation
from pygraphc.evaluation.SilhouetteIndex import SilhouetteIndex
from pygraphc.evaluation.DunnIndex import DunnIndex
from pygraphc.anomaly.AnomalyScore import AnomalyScore
from pygraphc.anomaly.SentimentAnalysis import SentimentAnalysis
from pygraphc.output.OutputText import OutputText
from pygraphc.similarity.LogTextSimilarity import LogTextSimilarity


def get_dataset(dataset, dataset_path, anomaly_path, file_extension, method):
    # get all log files under dataset directory
    matches = []
    # Debian-based: /var/log/auth.log
    auth_dataset = ['Hofstede2014', 'SecRepo', 'forensic-challenge-2010', 'Kippo']
    secure_dataset = ['hnet-hon-2004', 'hnet-hon-2006', 'forensic-challenge-2010-syslog', 'BlueGene2006', 'ras',
                      'illustration', 'vpn']
    if dataset in auth_dataset:
        for root, dirnames, filenames in os.walk(dataset_path):
            for filename in fnmatch.filter(filenames, file_extension):
                matches.append(os.path.join(root, filename))
    # RedHat-based: /var/log/secure
    elif dataset in secure_dataset:
        file_lists = os.listdir(dataset_path)
        matches = [dataset_path + '/' + filename for filename in file_lists if not filename.endswith('.labeled')]

    # get file name to save all of the results
    files = {}
    result_path = '/home/hudan/Git/pygraphc/result/' + method + '/'
    result_path2 = '/home/hudan/cosine/' + method + '/'
    for match in matches:
        identifier = match.split(dataset)
        index = dataset + identifier[1]
        log_path = match.split('/')[-1] if method == 'IPLoM' or method == 'LKE' else match
        files[index] = {'log_path': log_path, 'labeled_path': str(match) + '.labeled',
                        'result_percluster': result_path + index + '.percluster',
                        'result_perline': result_path + index + '.perline',
                        'anomaly_report': result_path + index + '.anomaly.csv',
                        'anomaly_perline': result_path + index + '.anomaly.perline.txt',
                        'anomaly_groundtruth': anomaly_path + match.split('/')[-1] + '.attack',
                        'result_path': result_path,
                        'cosine_path': result_path2 + index + '-',
                        'cosine_master_path': result_path2 + index + '-master-',
                        'cluster_pickle': result_path + index + '-cluster.pickle',
                        'illustration_csv': result_path + index + 'illustration.csv',
                        'illustration_csv_opt': result_path + index + '.illustration_opt.csv',
                        'logcluster_output': result_path + index + '.logcluster_output.txt',
                        'logcluster_outlier': result_path + index + '.logcluster_outlier.txt'}

    # file to save evaluation performance per method
    evaluation_file = result_path + dataset + '.evaluation.csv'

    return files, evaluation_file


def get_evaluation(evaluated_graph, clusters, logs, properties, year, edges_dict, log_type):
    # get prediction file
    ExternalEvaluation.set_cluster_label_id(evaluated_graph, clusters, logs, properties['result_perline'], log_type)

    # get sentiment analysis
    sentiment = SentimentAnalysis(evaluated_graph, clusters)
    sentiment.get_cluster_message()
    sentiment_score = sentiment.get_sentiment()

    # get anomaly score
    anomaly = AnomalyScore(evaluated_graph, clusters, year, edges_dict, sentiment_score, log_type)
    anomaly.get_anomaly_score()

    # please check this flag: False means without sentiment analysis included
    anomaly.get_anomaly_decision(False)

    # get anomaly-related value
    score = anomaly.anomaly_score
    cluster_property = anomaly.property
    cluster_abstraction = anomaly.abstraction
    quadratic_score = anomaly.quadratic_score
    normalized_score = anomaly.normalization_score
    anomaly_decision = anomaly.anomaly_decision

    # get evaluation of clustering performance
    ar = ExternalEvaluation.get_adjusted_rand(properties['labeled_path'], properties['result_perline'])
    ami = ExternalEvaluation.get_adjusted_mutual_info(properties['labeled_path'], properties['result_perline'])
    nmi = ExternalEvaluation.get_normalized_mutual_info(properties['labeled_path'], properties['result_perline'])
    h = ExternalEvaluation.get_homogeneity(properties['labeled_path'], properties['result_perline'])
    c = ExternalEvaluation.get_completeness(properties['labeled_path'], properties['result_perline'])
    v = ExternalEvaluation.get_vmeasure(properties['labeled_path'], properties['result_perline'])
    silhoutte_index = InternalEvaluation.get_silhoutte_index(evaluated_graph, clusters)

    # arrange dictionary of evaluation metrics
    evaluation_metrics = {
        'adj_rand_score': ar, 'adj_mutual_info_score': ami, 'norm_mutual_info_score': nmi,
        'homogeneity': h, 'completeness': c, 'vmeasure': v,
        'silhoutte_index': silhoutte_index
    }

    # get output per cluster, cluster property, and anomaly score
    OutputText.txt_percluster(properties['result_percluster'], clusters, 'graph', evaluated_graph, logs)
    OutputText.csv_cluster_property(properties['anomaly_report'], cluster_property, cluster_abstraction, score,
                                    quadratic_score, normalized_score, sentiment_score, anomaly_decision,
                                    evaluation_metrics)
    OutputText.txt_anomaly_perline(anomaly_decision, clusters, evaluated_graph, properties['anomaly_perline'], logs)

    # get evaluation of anomaly detection
    anomaly_ar = ExternalEvaluation.get_adjusted_rand(properties['anomaly_groundtruth'], properties['anomaly_perline'])
    anomaly_ami = ExternalEvaluation.get_adjusted_mutual_info(properties['anomaly_groundtruth'],
                                                              properties['anomaly_perline'])
    anomaly_nmi = ExternalEvaluation.get_normalized_mutual_info(properties['anomaly_groundtruth'],
                                                                properties['anomaly_perline'])
    anomaly_h = ExternalEvaluation.get_homogeneity(properties['anomaly_groundtruth'], properties['anomaly_perline'])
    anomaly_c = ExternalEvaluation.get_completeness(properties['anomaly_groundtruth'], properties['anomaly_perline'])
    anomaly_v = ExternalEvaluation.get_vmeasure(properties['anomaly_groundtruth'], properties['anomaly_perline'])
    anomaly_evaluation = (anomaly_ar, anomaly_ami, anomaly_nmi, anomaly_h, anomaly_c, anomaly_v)

    return ar, ami, nmi, h, c, v, silhoutte_index, anomaly_evaluation


def get_external_evaluation(evaluated_graph, clusters, logs, properties, log_type):
    # this method is for IPLoM, LKE, and PySplunk
    # get prediction file
    ExternalEvaluation.set_cluster_label_id(evaluated_graph, clusters, logs, properties['result_perline'], log_type)

    # get evaluation of clustering performance
    ar = ExternalEvaluation.get_adjusted_rand(properties['labeled_path'], properties['result_perline'])
    ami = ExternalEvaluation.get_adjusted_mutual_info(properties['labeled_path'], properties['result_perline'])
    nmi = ExternalEvaluation.get_normalized_mutual_info(properties['labeled_path'], properties['result_perline'])
    h = ExternalEvaluation.get_homogeneity(properties['labeled_path'], properties['result_perline'])
    c = ExternalEvaluation.get_completeness(properties['labeled_path'], properties['result_perline'])
    v = ExternalEvaluation.get_vmeasure(properties['labeled_path'], properties['result_perline'])

    return ar, ami, nmi, h, c, v


def get_internal_evaluation(evaluated_graph, clusters, logs, properties, mode, logtype):
    silhoutte_index, dunn_index = 0., 0.
    if mode == 'graph':
        silhoutte_index = InternalEvaluation.get_silhoutte_index(clusters, mode, evaluated_graph)
        dunn_index = InternalEvaluation.get_dunn_index(clusters, mode, evaluated_graph)
        OutputText.txt_percluster(properties['result_percluster'], clusters, mode, evaluated_graph, logs)
    elif mode == 'text':
        lts = LogTextSimilarity(mode, logtype, logs, clusters)
        cosine_similarity = lts.get_cosine_similarity()
        silhoutte_index = InternalEvaluation.get_silhoutte_index(clusters, mode, None, cosine_similarity)
        dunn_index = InternalEvaluation.get_dunn_index(clusters, mode, None, cosine_similarity)
        OutputText.txt_percluster(properties['result_percluster'], clusters, mode, None, logs)
    elif mode == 'text-csv':
        # calculate similarity inter and intra cluster
        lts = LogTextSimilarity(mode, logtype, logs, clusters, properties['cosine_path'])
        lts.get_cosine_similarity()

        # get internal evaluation
        si = SilhouetteIndex(mode, clusters, properties['cosine_path'])
        silhoutte_index = si.get_silhouette_index()
        di = DunnIndex(mode, clusters, properties['cosine_path'])
        dunn_index = di.get_dunn_index()

        # write to file
        OutputText.txt_percluster(properties['result_percluster'], clusters, mode, None, logs)

    return silhoutte_index, dunn_index


def get_confusion(properties):
    return ExternalEvaluation.get_confusion(properties['anomaly_groundtruth'], properties['anomaly_perline'])


def main(dataset, year, method, log_type, evaluation, illustration):
    # list of methods
    graph_method = ['connected_components', 'max_clique', 'max_clique_weighted', 'max_clique_weighted_sa',
                    'kclique_percolation', 'kclique_percolation_weighted', 'majorclust', 'improved_majorclust',
                    'improved_majorclust_wo_refine']
    # nongraph_method = ['IPLoM', 'LKE']

    # get dataset files
    master_path = '/home/hudan/Git/labeled-authlog/dataset/'
    dataset_path = {
        'Hofstede2014': master_path + 'Hofstede2014/dataset1_perday',
        'SecRepo': master_path + 'SecRepo/auth-perday',
        'forensic-challenge-2010': master_path + 'Honeynet/forensic-challenge-5-2010/forensic-challenge-5-2010-perday',
        'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-perday',
        'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-perday',
        'Kippo': master_path + 'Kippo/per_day',
        'forensic-challenge-2010-syslog':
            master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-2010-syslog/all',
        'BlueGene2006': master_path + 'BlueGene2006/per_day',
        'ras': master_path + 'ras/per_day',
        'illustration': master_path + 'illustration/per_day',
        'vpn': master_path + 'vpn/per_day'
    }

    # anomaly dataset
    anomaly_path = {
        'Hofstede2014': master_path + 'Hofstede2014/dataset1_attack/',
        'SecRepo': master_path + 'SecRepo/auth-attack/',
        'forensic-challenge-2010': master_path + 'Honeynet/forensic-challenge-2010/forensic-challenge-5-2010-attack/',
        'hnet-hon-2004': master_path + 'Honeynet/honeypot/hnet-hon-2004/hnet-hon-10122004-var-attack/',
        'hnet-hon-2006': master_path + 'Honeynet/honeypot/hnet-hon-2006/hnet-hon-var-log-02282006-attack/',
        'Kippo': master_path + 'Kippo/attack/',
        'forensic-challenge-2010-syslog': '',
        'BlueGene2006': '',
        'ras': '',
        'illustration': master_path + 'illustration/attack/',
        'vpn': ''
    }

    # note that in RedHat-based authentication log, parameter '*.log' is not used
    files, evaluation_file = get_dataset(dataset, dataset_path[dataset], anomaly_path[dataset], '*.log', method)

    # open evaluation file
    f = open(evaluation_file, 'wt')
    writer = csv.writer(f)

    # set header
    header = ('file_name', 'adjusted_rand', 'adjusted_mutual_info', 'normalized_mutual_info',
              'homogeneity', 'completeness', 'v-measure', 'tp', 'fp', 'fn', 'tn',
              'precision', 'recall', 'accuracy', 'silhoutte_index', 'dunn_index', 'k', 'I')
    writer.writerow(header)

    # main process
    for file_identifier, properties in files.iteritems():
        print file_identifier
        # initialization
        ar, ami, nmi, h, c, v = 0., 0., 0., 0., 0., 0.
        silhoutte, dunn = 0., 0.
        true_false, precision, recall, accuracy = [], 0., 0., 0.
        edges_weight, nodes_id = [], []
        best_parameter = {'k': 0., 'I': 0.}

        if method in graph_method:
            # preprocess log file
            preprocess = PreprocessLog(log_type, properties['log_path'])
            if log_type == 'auth':
                preprocess.do_preprocess()  # auth
            elif log_type == 'kippo' or log_type == 'syslog' or log_type == 'bluegene-logs' or log_type == 'raslog' \
                    or log_type == 'vpnlog':
                preprocess.preprocess()
            events_unique = preprocess.events_unique
            original_logs = preprocess.logs

            # create graph
            g = CreateGraph(events_unique)
            g.do_create()
            graph = g.g
            edges_weight = g.edges_weight
            edges_dict = g.edges_dict
            nodes_id = g.get_nodes_id()

        if method == 'majorclust':
            # run MajorClust method
            mc = MajorClust(graph)
            mc_clusters = mc.get_majorclust(graph)

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, mc_clusters, original_logs,
                                                                                  properties, year, edges_dict,
                                                                                  log_type)
            true_false, specificity, precision, recall, accuracy = get_confusion(properties)
            nx.write_dot(graph, 'illustration.dot')
            graph.clear()

        elif method == 'improved_majorclust':
            # run ImprovedMajorClust method
            imc = ImprovedMajorClust(graph)
            imc_clusters = imc.get_improved_majorclust()

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, imc_clusters, original_logs,
                                                                                  properties, year, edges_dict,
                                                                                  log_type)
            true_false, specificity, precision, recall, accuracy = get_confusion(properties)
            nx.write_dot(graph, 'illustration.dot')
            graph.clear()

        elif method == 'improved_majorclust_wo_refine':
            # run ImprovedMajorClust without refine phase
            imcwr = ImprovedMajorClust(graph)
            imcwr_clusters = imcwr.get_improved_majorclust_wo_refine()

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, imcwr_clusters, original_logs,
                                                                                  properties, year, edges_dict,
                                                                                  log_type)
            true_false, specificity, precision, recall, accuracy = get_confusion(properties)
            graph.clear()

        elif method == 'graph_entropy':
            # preprocess
            preprocess = CreateGraphModel(properties['log_path'])
            graph = preprocess.create_graph()

            # run GraphEntropy method
            ge = GraphEntropy(graph)
            ge_clusters = ge.get_graph_entropy()
            print ge_clusters

            # do evaluation performance and clear graph
            if evaluation['external']:
                ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, ge_clusters, original_logs,
                                                                                      properties, year, edges_dict,
                                                                                      log_type)
            elif evaluation['internal']:
                ar, ami, nmi, h, c, v, anomaly_evaluation = 0., 0., 0., 0., 0., 0., ()
                true_false, specificity, precision, recall, accuracy = [0., 0., 0., 0.], 0., 0., 0., 0.
                silhoutte, dunn = 0., 0.

            nx.write_dot(graph, 'dec.dot')
            graph.clear()

        elif method == 'max_clique_weighted':
            k, threshold = 2, 0.1
            maxc = MaxCliquesPercolationWeighted(graph, edges_weight, nodes_id)
            maxc.init_maxclique_percolation()
            maxc_clusters = maxc.get_maxcliques_percolation_weighted(k, threshold)

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, maxc_clusters, original_logs,
                                                                                  properties, year, edges_dict,
                                                                                  log_type)
            true_false, specificity, precision, recall, accuracy = get_confusion(properties)
            graph.clear()

        elif method == 'max_clique_weighted_sa':
            # Selim et al., 1991, Sun et al., 1996
            tmin = 10 ** (-99)
            tmax = 10.
            alpha = 0.9

            energy_type = 'dunn'
            iteration_threshold = 0.3   # only xx% of total trial with brute-force
            brute_force = False
            maxc_sa = MaxCliquesPercolationSA(graph, edges_weight, nodes_id, tmin, tmax, alpha,
                                              energy_type, iteration_threshold, brute_force)
            maxc_sa.init_maxclique_percolation()
            best_parameter, maxc_sa_cluster, best_energy = maxc_sa.get_maxcliques_sa()

            # do evaluation performance and clear graph
            if evaluation['external']:
                ar, ami, nmi, h, c, v, silhoutte, anomaly_evaluation = get_evaluation(graph, maxc_sa_cluster,
                                                                                      original_logs,
                                                                                      properties, year, edges_dict,
                                                                                      log_type)
                true_false, specificity, precision, recall, accuracy = get_confusion(properties)

            elif evaluation['internal']:
                ar, ami, nmi, h, c, v, anomaly_evaluation = 0., 0., 0., 0., 0., 0., ()
                true_false, specificity, precision, recall, accuracy = [0., 0., 0., 0.], 0., 0., 0., 0.
                silhoutte, dunn = get_internal_evaluation(graph, maxc_sa_cluster, original_logs, properties, 'graph',
                                                          log_type)

            if illustration:
                with open(properties['illustration_csv_opt'], 'wb') as fi:
                    writer2 = csv.writer(fi)
                    writer2.writerow((best_parameter['k'], best_parameter['I'], -1 * best_energy))

            # nx.write_dot(graph, 'dec.dot')
            graph.clear()

        elif method == 'IPLoM':
            # call IPLoM and get clusters
            print properties['log_path']
            para = ParaIPLoM(path=dataset_path[dataset] + '/', logname=properties['log_path'],
                             save_path=properties['result_path'])
            myparser = IPLoM(para)
            myparser.main_process()
            iplom_clusters = myparser.get_clusters()
            original_logs = myparser.logs
            mode = 'text-csv'

            # do evaluation performance
            if evaluation['external']:
                ar, ami, nmi, h, c, v = get_external_evaluation(None, iplom_clusters, original_logs, properties,
                                                                log_type)
            elif evaluation['internal']:
                ar, ami, nmi, h, c, v, anomaly_evaluation = 0., 0., 0., 0., 0., 0., ()
                true_false, specificity, precision, recall, accuracy = [0., 0., 0., 0.], 0., 0., 0., 0.
                silhoutte, dunn = get_internal_evaluation(None, iplom_clusters, original_logs, properties, mode,
                                                          log_type)

        elif method == 'LKE':
            print properties['log_path']
            para = Para(path=dataset_path[dataset] + '/', logname=properties['log_path'],
                        save_path=properties['result_path'])
            myparser = LKE(para)
            myparser.main_process()
            lke_clusters = myparser.get_clusters()
            original_logs = myparser.logs

            # do evaluation performance
            ar, ami, nmi, h, c, v = get_external_evaluation(None, lke_clusters, original_logs, properties, log_type)

        # write evaluation result to file
        row = ('/'.join(properties['log_path'].split('/')[-2:]), ar, ami, nmi, h, c, v,
               true_false[0], true_false[1], true_false[2], true_false[3], precision, recall, accuracy,
               silhoutte, dunn, best_parameter['k'], best_parameter['I'])
        writer.writerow(row)

    f.close()

if __name__ == '__main__':
    # available datasets: Hofstede2014, SecRepo, forensic-challenge-2010, hnet-hon-2004, hnet-hon-2006, Kippo,
    #                     forensic-challenge-2010-syslog, bluegene, ras
    # available log type: auth, kippo, syslog, bluegene-logs, raslog
    # available methods : majorclust, improved_majorclust, graph_entropy, max_clique_weighted, IPLoM, LKE
    #                     improved_majorclust_wo_refine, max_clique_weighted_sa
    start = time()
    syslog_config = {
        'data': 'forensic-challenge-2010-syslog',
        'logtype': 'syslog',
        'year': 2009,
        'method': 'IPLoM',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    kippo_config = {
        'data': 'Kippo',
        'logtype': 'kippo',
        'year': 2017,
        'method': 'max_clique_weighted_sa',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    ras_config = {
        'data': 'ras',
        'logtype': 'raslog',
        'year': 2009,
        'method': 'IPLoM',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    auth_config = {
        'data': 'Hofstede2014',
        'logtype': 'auth',
        'year': 2014,
        'method': 'max_clique_weighted_sa',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    illustration_config = {
        'data': 'illustration',
        'logtype': 'auth',
        'year': '2014',
        'method': 'graph_entropy',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': True
    }

    bluegene_config = {
        'data': 'BlueGene2006',
        'logtype': 'bluegene',
        'year': 2005,
        'method': 'IPLoM',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    vpn_config = {
        'data': 'vpn',
        'logtype': 'vpnlog',
        'year': 2012,
        'method': 'max_clique_weighted_sa',
        'evaluation': {
            'external': False,
            'internal': True
        },
        'anomaly': {
            'statistics': False,
            'sentiment': False
        },
        'illustration': False
    }

    # change this line to switch to other datasets
    config = illustration_config

    # run experiment
    main(config['data'], config['year'], config['method'], config['logtype'], config['evaluation'],
         config['illustration'])

    # print runtime
    duration = time() - start
    minute, second = divmod(duration, 60)
    hour, minute = divmod(minute, 60)
    print "Runtime: %d:%02d:%02d" % (hour, minute, second)
