import fnmatch
import os
import csv
from time import time
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.clustering.GraphEntropy import GraphEntropy
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation
from pygraphc.evaluation.InternalEvaluation import InternalEvaluation
from pygraphc.anomaly.AnomalyScore import AnomalyScore
from pygraphc.output.Output import Output


def get_dataset(dataset, dataset_path, file_extension, method):
    # get all log files under dataset directory
    matches = []
    for root, dirnames, filenames in os.walk(dataset_path):
        for filename in fnmatch.filter(filenames, file_extension):
            matches.append(os.path.join(root, filename))

    # get file name to save all of the results
    files = {}
    result_path = '/home/hudan/Git/pygraphc/result/' + method + '/'
    for match in matches:
        identifier = match.split(dataset)
        index = dataset + identifier[1]
        files[index] = {'log_path': match, 'labeled_path': str(match) + '.labeled',
                        'result_percluster': result_path + index + '.percluster',
                        'result_perline': result_path + index + '.perline',
                        'anomaly_report': result_path + index + '.anomaly.csv'}

    # file to save evaluation performance per method
    evaluation_file = result_path + dataset + '.evaluation.csv'

    return files, evaluation_file


def get_evaluation(evaluated_graph, clusters, logs, properties, year, edges_dict):
    # get prediction file
    ExternalEvaluation.set_cluster_label_id(evaluated_graph, clusters, logs, properties['result_perline'])

    # get anomaly score
    anomaly_score = AnomalyScore(evaluated_graph, clusters, properties['anomaly_report'], year, edges_dict)
    anomaly_score.write_property()

    # get output
    output_txt = Output(evaluated_graph, clusters, logs, properties['result_percluster'])
    output_txt.to_txt()

    # get evaluation of clustering performance
    ar = ExternalEvaluation.get_adjusted_rand(properties['labeled_path'], properties['result_perline'])
    ami = ExternalEvaluation.get_adjusted_mutual_info(properties['labeled_path'], properties['result_perline'])
    nmi = ExternalEvaluation.get_normalized_mutual_info(properties['labeled_path'], properties['result_perline'])
    h = ExternalEvaluation.get_homogeneity(properties['labeled_path'], properties['result_perline'])
    c = ExternalEvaluation.get_completeness(properties['labeled_path'], properties['result_perline'])
    v = ExternalEvaluation.get_vmeasure(properties['labeled_path'], properties['result_perline'])
    silhoutte_index = InternalEvaluation.get_silhoutte_index(evaluated_graph, clusters)

    return ar, ami, nmi, h, c, v, silhoutte_index


def main(dataset, year, method):
    # get dataset files
    files = {}
    evaluation_file = ''
    if dataset == 'Hofstede2014':
        files, evaluation_file = get_dataset(dataset,
                                             '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014/dataset1_perday',
                                             '*.log', method)
    elif dataset == 'SecRepo':
        files, evaluation_file = get_dataset(dataset, '/home/hudan/Git/labeled-authlog/dataset/SecRepo',
                                             '*.log', method)

    # open evaluation file
    f = open(evaluation_file, 'wt')
    writer = csv.writer(f)

    # set header
    header = ('file_name', 'adjusted_rand', 'adjusted_mutual_info', 'normalized_mutual_info',
              'homogeneity', 'completeness', 'v-measure', 'silhoutte_index')
    writer.writerow(header)

    # main process
    for file_identifier, properties in files.iteritems():
        # preprocess log file
        preprocess = PreprocessLog(properties['log_path'])
        preprocess.do_preprocess()
        events_unique = preprocess.events_unique
        original_logs = preprocess.logs

        # create graph
        g = CreateGraph(events_unique)
        g.do_create()
        graph = g.g
        edges_dict = g.edges_dict

        # initialization
        ar, ami, nmi, h, c, v, silhoutte = 0., 0., 0., 0., 0., 0., 0.

        if method == 'majorclust':
            # run MajorClust method
            mc_graph = graph.copy()
            mc = MajorClust(mc_graph)
            mc_clusters = mc.get_majorclust(graph)

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte = get_evaluation(mc_graph, mc_clusters, original_logs, properties,
                                                              year, edges_dict)
            mc_graph.clear()

        elif method == 'improved_majorclust':
            # run ImprovedMajorClust method
            imc_graph = graph.copy()
            imc = ImprovedMajorClust(imc_graph)
            imc_clusters = imc.get_improved_majorclust()

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte = get_evaluation(imc_graph, imc_clusters, original_logs, properties,
                                                              year, edges_dict)
            imc_graph.clear()

        elif method == 'graph_entropy':
            # run GraphEntropy method
            ge_graph = graph.copy()
            ge = GraphEntropy(ge_graph)
            ge_clusters = ge.get_graph_entropy()

            # do evaluation performance and clear graph
            ar, ami, nmi, h, c, v, silhoutte = get_evaluation(ge_graph, ge_clusters, original_logs, properties,
                                                              year, edges_dict)
            ge_graph.clear()

        # writer evaluation result to file
        row = ('/'.join(properties['log_path'].split('/')[-2:]), ar, ami, nmi, h, c, v, silhoutte)
        writer.writerow(row)

    f.close()

if __name__ == '__main__':
    start = time()
    data = 'Hofstede2014'
    clustering_method = 'improved_majorclust'
    main(data, '2014', clustering_method)
    duration = time() - start
    print 'Runtime:', duration, 'seconds'
