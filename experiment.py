import fnmatch
import os
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust


def get_dataset(dataset, dataset_path, file_extension):
    # get all log files under dataset directory
    matches = []
    for root, dirnames, filenames in os.walk(dataset_path):
        for filename in fnmatch.filter(filenames, file_extension):
            matches.append(os.path.join(root, filename))

    # get file identifier, log file, labeled log file, result per cluster, result per line, and anomaly report
    files = {}
    result_path = './result/'
    for match in matches:
        identifier = match.split(dataset)
        index = dataset + identifier[1]
        files[index] = {'log_path': match, 'labeled_path': str(match) + '.labeled',
                        'result_percluster': result_path + index + '.percluster',
                        'result_perline': result_path + index + '.perline',
                        'anomaly_report': result_path + index + '.anomaly'}

    return files


def main(dataset):
    # get dataset files
    files = {}
    if dataset == 'Hofstede2014':
        files = get_dataset(dataset, '/home/hudan/Git/labeled-authlog/dataset/Hofstede2014', '*.anon')
    elif dataset == 'SecRepo':
        files = get_dataset(dataset, '/home/hudan/Git/labeled-authlog/dataset/SecRepo', '*.log')

    # main process
    for file_identifier, properties in files.iteritems():
        # preprocess log file
        preprocess = PreprocessLog(properties['log_path'])
        preprocess.do_preprocess()
        events_unique = preprocess.events_unique

        # create graph
        g = CreateGraph(events_unique)
        g.do_create()
        graph = g.g

        # run MajorClust method
        mc = MajorClust(graph)
        clusters = mc.get_majorclust(graph)
        print clusters

if __name__ == '__main__':
    data = 'Hofstede2014'
    main(data)
