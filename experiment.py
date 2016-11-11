import fnmatch
import os
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.clustering.GraphEntropy import GraphEntropy
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation
from pygraphc.anomaly.AnomalyScore import AnomalyScore
from pygraphc.output.Output import Output


def get_dataset(dataset, dataset_path, file_extension, method):
    # get all log files under dataset directory
    matches = []
    for root, dirnames, filenames in os.walk(dataset_path):
        for filename in fnmatch.filter(filenames, file_extension):
            matches.append(os.path.join(root, filename))

    # get file identifier, log file, labeled log file, result per cluster, result per line, and anomaly report
    files = {}
    result_path = './result/' + method + '/'
    for match in matches:
        identifier = match.split(dataset)
        index = dataset + identifier[1]
        files[index] = {'log_path': match, 'labeled_path': str(match) + '.labeled',
                        'result_percluster': result_path + index + '.percluster',
                        'result_perline': result_path + index + '.perline',
                        'anomaly_report': result_path + index + '.anomaly'}

    return files


def get_evaluation(evaluated_graph, clusters, logs, properties, year):
    # get prediction file
    ExternalEvaluation.set_cluster_label_id(evaluated_graph, clusters, logs, properties['result_perline'])

    # get anomaly score
    anomaly_score = AnomalyScore(evaluated_graph, clusters, properties['anomaly_report'], year)
    anomaly_score.write_property()

    # get output
    output_txt = Output(evaluated_graph, clusters, logs, properties['result_percluster'])
    output_txt.to_txt()

    # get evaluation of clustering performance
    adj_rand_score = ExternalEvaluation.get_adjusted_rand_score(properties['labeled_path'],
                                                                properties['result_perline'])
    adj_mutual_info_score = ExternalEvaluation.get_adjusted_mutual_info_score(properties['labeled_path'],
                                                                              properties['result_perline'])
    norm_mutual_info_score = ExternalEvaluation.get_normalized_mutual_info_score(properties['labeled_path'],
                                                                                 properties['result_perline'])
    homogeneity_completeness_vmeasure = ExternalEvaluation.get_homogeneity_completeness_vmeasure(
        properties['labeled_path'], properties['result_perline'])

    return adj_rand_score, adj_mutual_info_score, norm_mutual_info_score, homogeneity_completeness_vmeasure


def main(dataset, year, method):
    # get dataset files
    files = {}
    if dataset == 'Hofstede2014':
        files = get_dataset(dataset, '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014', '*.anon', method)
    elif dataset == 'SecRepo':
        files = get_dataset(dataset, '/home/hudan/Git/labeled-authlog/dataset/SecRepo', '*.log', method)

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

        if method == 'majorclust':
            # run MajorClust method
            mc_graph = graph.copy()
            mc = MajorClust(mc_graph)
            mc_clusters = mc.get_majorclust(graph)

            # do evaluation performance and clear graph
            get_evaluation(mc_graph, mc_clusters, original_logs, properties, year)
            mc_graph.clear()

        elif method == 'improved_majorclust':
            # run ImprovedMajorClust method
            imc_graph = graph.copy()
            imc = ImprovedMajorClust(imc_graph)
            imc_clusters = imc.get_improved_majorclust()

            # do evaluation performance and clear graph
            get_evaluation(imc_graph, imc_clusters, original_logs, properties, year)
            imc_graph.clear()

        elif method == 'graph_entropy':
            # run GraphEntropy method
            ge_graph = graph.copy()
            ge = GraphEntropy(ge_graph)
            ge_clusters = ge.get_graph_entropy()

            # do evaluation performance and clear graph
            get_evaluation(ge_graph, ge_clusters, original_logs, properties, year)
            ge_graph.clear()


if __name__ == '__main__':
    data = 'Hofstede2014'
    clustering_method = 'improved_majorclust'
    main(data, '2014', clustering_method)
