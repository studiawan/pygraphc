import os
import errno
import fnmatch
import csv
import multiprocessing
import multiprocessing.pool
from time import time
from operator import itemgetter
from ConfigParser import SafeConfigParser
from numpy import linspace
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.MaxCliquesPercolationSA import MaxCliquesPercolationSA
from pygraphc.clustering.MajorClust import MajorClust, ImprovedMajorClust
from pygraphc.evaluation.EvaluationUtility import EvaluationUtility
from pygraphc.evaluation.CalinskiHarabaszIndex import CalinskiHarabaszIndex
from pygraphc.evaluation.DaviesBouldinIndex import DaviesBouldinIndex
from pygraphc.evaluation.XieBeniIndex import XieBeniIndex
from pygraphc.misc.IPLoM import ParaIPLoM, IPLoM
from pygraphc.misc.LogSig import Para, LogSig
from pygraphc.misc.LKE import ParaLKE, LKE
from pygraphc.misc.LogCluster import LogCluster
from pygraphc.output.OutputText import OutputText


class ClusteringExperiment(object):
    def __init__(self, method):
        self.method = method
        self.configuration = {}
        self.methods = {}
        self.files = {}

    def __read_config(self):
        # read configuration file to run an experiment based on a specific method and a dataset
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', 'clustering', self.method + '.conf')
        parser.read(config_path)

        for section_name in parser.sections():
            options = {}
            for name, value in parser.items(section_name):
                options[name] = value
            self.configuration[section_name] = options

    def __get_dataset(self):
        # get all log files under dataset directory
        dataset = self.configuration['main']['dataset']
        dataset_path = self.configuration[dataset]['path']
        file_extension = self.configuration[dataset]['file_extension']
        matches = []
        for root, dirnames, filenames in os.walk(dataset_path):
            for filename in fnmatch.filter(filenames, file_extension):
                full_path = os.path.join(root, filename)
                matches.append((full_path, filename))

        # set experiment result path and a single log file path
        result_path = self.configuration['experiment_result_path']['result_path']
        for full_path, filename in matches:
            self.files[filename] = {
                'result_path': result_path,
                'log_path': full_path
            }

        if self.configuration['main']['clustering'] == '1':
            for full_path, filename in matches:
                # get all files for clustering
                properties = {}
                for key, value in self.configuration['clustering_result_path'].iteritems():
                    directory = os.path.join(result_path, dataset, value)
                    self.__check_path(directory)
                    properties[key] = os.path.join(directory, filename)

                # update files dictionary
                self.files[filename].update(properties)

                # get evaluation directory and file for clustering
                self.files['evaluation_directory'] = \
                    os.path.join(result_path, dataset,
                                 self.configuration['clustering_evaluation']['evaluation_directory'])
                self.files['evaluation_file'] = \
                    os.path.join(result_path, dataset,
                                 self.configuration['clustering_evaluation']['evaluation_directory'],
                                 self.configuration['clustering_evaluation']['evaluation_file'])

    def __get_methods(self):
        # get all of available methods from config file
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', 'clustering', 'method.conf')
        parser.read(config_path)

        for section_name in parser.sections():
            options, methods = {}, []
            for name, value in parser.items(section_name):
                options[name] = value
                methods = options[name].split('\n')
            self.methods[section_name] = methods

    def __get_internal_evaluation(self, new_clusters, preprocessed_logs, log_length):
        # note that order of evaluation matter
        internal_evaluation = []
        if self.configuration['internal_evaluation']['calinski_harabasz'] == '1':
            ch = CalinskiHarabaszIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(ch.get_calinski_harabasz())
        if self.configuration['internal_evaluation']['davies_bouldin'] == '1':
            db = DaviesBouldinIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(db.get_davies_bouldin())
        if self.configuration['internal_evaluation']['xie_beni'] == '1':
            xb = XieBeniIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(xb.get_xie_beni())

        return tuple(internal_evaluation)

    @staticmethod
    def __check_path(path):
        # check a path is exist or not. if not exist, then create it
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def __get_clustering(self, filename_properties):
        # run the experiment
        filename = filename_properties[0]
        properties = filename_properties[1]
        row = ()

        if filename != 'evaluation_directory' and filename != 'evaluation_file':
            if self.method in self.methods['graph']:
                new_clusters, original_logs = {}, []

                if self.method == 'max_clique_weighted_sa':
                    # preprocess log file and create graph
                    preprocess = CreateGraphModel(properties['log_path'])
                    graph = preprocess.create_graph()
                    edges_weight = preprocess.edges_weight
                    nodes_id = range(preprocess.unique_events_length)
                    preprocessed_logs = preprocess.preprocessed_logs
                    log_length = preprocess.log_length
                    original_logs = preprocess.logs

                    # initialize parameter for simulated annealing
                    # Selim et al., 1991, Sun et al., 1996
                    tmin = 10 ** (-99)
                    tmax = 10.
                    alpha = 0.9
                    energy_type = 'calinski_harabasz'
                    iteration_threshold = 0.3  # only xx% of total trial with brute-force
                    brute_force = False

                    # run maximal clique weighted with simulated annealing
                    maxc_sa = MaxCliquesPercolationSA(graph, edges_weight, nodes_id, tmin, tmax, alpha,
                                                      energy_type, iteration_threshold, brute_force,
                                                      preprocessed_logs, log_length)
                    maxc_sa.init_maxclique_percolation()
                    best_parameter, maxc_sa_cluster, best_energy = maxc_sa.get_maxcliques_sa()

                    # get internal evaluation
                    # convert clustering result from graph to text
                    new_clusters = EvaluationUtility.convert_to_text(graph, maxc_sa_cluster)
                    internal_evaluation = self.__get_internal_evaluation(new_clusters, preprocessed_logs, log_length)
                    print filename, internal_evaluation

                    # write experiment result and close evaluation file
                    if 'k' not in best_parameter.keys():
                        best_parameter['k'] = -1
                    if 'I' not in best_parameter.keys():
                        best_parameter['I'] = -1

                    row = (filename, ) + internal_evaluation + (best_parameter['k'], best_parameter['I'])
                    graph.clear()

                elif self.method == 'majorclust':
                    # preprocess log file
                    log_type = self.configuration[self.configuration['main']['dataset']]['log_type']
                    preprocess = PreprocessLog(log_type, properties['log_path'])
                    if log_type == 'auth':
                        preprocess.do_preprocess()  # auth
                    else:
                        preprocess.preprocess()

                    events_unique = preprocess.events_unique
                    log_length = preprocess.loglength
                    preprocessed_logs = preprocess.preprocessed_logs
                    original_logs = preprocess.logs

                    # create graph
                    g = CreateGraph(events_unique)
                    g.do_create()
                    graph = g.g

                    # run MajorClust
                    mc = MajorClust(graph)
                    clusters = mc.get_majorclust(graph)

                    # get internal evaluation
                    # convert clustering result from graph to text
                    new_clusters = EvaluationUtility.convert_to_text(graph, clusters)
                    internal_evaluation = self.__get_internal_evaluation(new_clusters, preprocessed_logs, log_length)
                    print filename, internal_evaluation

                    # write experiment result and close evaluation file
                    row = (filename,) + internal_evaluation
                    graph.clear()

                elif self.method == 'improved_majorclust':
                    # preprocess log file
                    log_type = self.configuration[self.configuration['main']['dataset']]['log_type']
                    preprocess = PreprocessLog(log_type, properties['log_path'])
                    if log_type == 'auth':
                        preprocess.do_preprocess()  # auth
                    else:
                        preprocess.preprocess()

                    events_unique = preprocess.events_unique
                    log_length = preprocess.loglength
                    preprocessed_logs = preprocess.preprocessed_logs
                    original_logs = preprocess.logs

                    # create graph
                    g = CreateGraph(events_unique)
                    g.do_create()
                    graph = g.g

                    # run improved MajorClust
                    imc = ImprovedMajorClust(graph)
                    clusters = imc.get_improved_majorclust()

                    # get internal evaluation
                    # convert clustering result from graph to text
                    new_clusters = EvaluationUtility.convert_to_text(graph, clusters)
                    internal_evaluation = self.__get_internal_evaluation(new_clusters, preprocessed_logs, log_length)
                    print filename, internal_evaluation

                    # write experiment result and close evaluation file
                    row = (filename, ) + internal_evaluation
                    graph.clear()

                # write clustering result per cluster to text file
                OutputText.percluster_with_logid(self.files[filename]['percluster_path'], new_clusters, original_logs)

            elif self.method in self.methods['non_graph']:
                clusters, original_logs = {}, []
                preprocessed_logs, log_length = {}, 0

                if self.method == 'LogCluster':
                    # initialization of parameters
                    rsupports = linspace(10, 90, 9)
                    log_file = self.files[filename]['log_path']
                    outlier_file = self.files[filename]['outlier_path']
                    output_file = self.files[filename]['output_path']
                    evaluation_results = []

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(log_file, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                    # run LogCluster clustering
                    lc = LogCluster(None, None, log_file, rsupports, outlier_file, output_file)
                    clusters_list = lc.get_clusters_manysupports()
                    for clusters in clusters_list:
                        evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                        evaluation_results.append([evaluation[0], clusters])

                    # choose the best evaluation
                    sorted_value = sorted(evaluation_results, key=itemgetter(0), reverse=True)
                    clusters = sorted_value[0][1]

                elif self.method == 'IPLoM':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = ParaIPLoM(path=dataset_path + '/', logname=filename,
                                     save_path=self.configuration['experiment_result_path']['result_path'])

                    # run IPLoM clustering
                    myiplom = IPLoM(para)
                    myiplom.main_process()
                    clusters = myiplom.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                elif self.method == 'LogSig':
                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    group_nums = range(2, 10, 1)
                    evaluation_results = []

                    for group_num in group_nums:
                        para = Para(path=dataset_path + '/', logname=filename,
                                    savePath=self.configuration['experiment_result_path']['result_path'],
                                    groupNum=group_num)  # check again about groupNum parameter

                        # run LogSig clustering
                        ls = LogSig(para)
                        ls.mainProcess()
                        clusters = ls.get_clusters()

                        # get evaluation
                        evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                        evaluation_results.append([evaluation[0], clusters])
                        print filename, group_num, evaluation

                    # choose the best evaluation
                    sorted_value = sorted(evaluation_results, key=itemgetter(0), reverse=True)
                    clusters = sorted_value[0][1]

                elif self.method == 'LKE':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = ParaLKE(path=dataset_path + '/', logname=filename, threshold2=5,
                                   save_path=self.configuration['experiment_result_path']['result_path'])

                    # run LKE clustering
                    lke = LKE(para)
                    lke.main_process()
                    clusters = lke.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                # get internal evaluation
                internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                row = (filename, ) + internal_evaluation
                print filename, internal_evaluation

                # write clustering result per cluster to text file
                OutputText.percluster_with_logid(self.files[filename]['percluster_path'], clusters, original_logs)

        return row

    def __call__(self, filename_properties):
        # main method called when running in multiprocessing
        return self.__get_clustering(filename_properties)

    def run_clustering(self):
        # initialization
        self.__get_methods()
        self.__read_config()
        self.__get_dataset()

        # get filename and properties
        filename_properties = []
        for filename, properties in self.files.iteritems():
            filename_properties.append((filename, properties))

        # run experiment in multiprocessing mode
        total_cpu = multiprocessing.cpu_count()
        # pool = multiprocessing.Pool(processes=total_cpu)
        pool = NoDaemonProcessPool(processes=total_cpu)
        results = pool.map(self, filename_properties)
        pool.close()
        pool.join()

        # open evaluation file
        self.__check_path(self.files['evaluation_directory'])
        f = open(self.files['evaluation_file'], 'wt')
        writer = csv.writer(f)

        # set header for evaluation file
        header = []
        if self.configuration['main']['clustering']:
            header = self.configuration['clustering_evaluation']['evaluation_file_header'].split('\n')
        writer.writerow(tuple(header))

        # write experiment result
        for result in results:
            writer.writerow(result)

        # close evaluation file
        f.close()

    def run_clustering_experiment(self):
        # initialization
        self.__get_methods()
        self.__read_config()
        self.__get_dataset()

        # open evaluation file
        self.__check_path(self.files['evaluation_directory'])
        f = open(self.files['evaluation_file'], 'wt')
        writer = csv.writer(f)

        # set header for evaluation file
        header = []
        if self.configuration['main']['clustering']:
            header = self.configuration['clustering_evaluation']['evaluation_file_header'].split('\n')
        writer.writerow(tuple(header))

        # run the experiment
        for filename, properties in self.files.iteritems():
            if filename == 'evaluation_directory' or filename == 'evaluation_file':
                continue

            if self.method in self.methods['graph']:
                new_clusters, original_logs = {}, []

                if self.method == 'max_clique_weighted_sa':
                    # preprocess log file and create graph
                    preprocess = CreateGraphModel(properties['log_path'])
                    graph = preprocess.create_graph()
                    edges_weight = preprocess.edges_weight
                    nodes_id = range(preprocess.unique_events_length)
                    preprocessed_logs = preprocess.preprocessed_logs
                    log_length = preprocess.log_length
                    original_logs = preprocess.logs

                    # initialize parameter for simulated annealing
                    # Selim et al., 1991, Sun et al., 1996
                    tmin = 10 ** (-99)
                    tmax = 10.
                    alpha = 0.9
                    energy_type = 'calinski_harabasz'
                    iteration_threshold = 0.3  # only xx% of total trial with brute-force
                    brute_force = False

                    # run maximal clique weighted with simulated annealing
                    maxc_sa = MaxCliquesPercolationSA(graph, edges_weight, nodes_id, tmin, tmax, alpha,
                                                      energy_type, iteration_threshold, brute_force,
                                                      preprocessed_logs, log_length)
                    maxc_sa.init_maxclique_percolation()
                    best_parameter, maxc_sa_cluster, best_energy = maxc_sa.get_maxcliques_sa()

                    # get internal evaluation
                    # convert clustering result from graph to text
                    new_clusters = EvaluationUtility.convert_to_text(graph, maxc_sa_cluster)
                    internal_evaluation = self.__get_internal_evaluation(new_clusters, preprocessed_logs, log_length)
                    print filename, internal_evaluation

                    # write experiment result and close evaluation file
                    row = (filename, ) + internal_evaluation + (best_parameter['k'], best_parameter['I'])
                    writer.writerow(row)
                    graph.clear()

                elif self.method == 'improved_majorclust':
                    # preprocess log file
                    log_type = self.configuration[self.configuration['main']['dataset']]['log_type']
                    preprocess = PreprocessLog(log_type, properties['log_path'])
                    if log_type == 'auth':
                        preprocess.do_preprocess()  # auth
                    else:
                        preprocess.preprocess()

                    events_unique = preprocess.events_unique
                    log_length = preprocess.loglength
                    preprocessed_logs = preprocess.preprocessed_logs
                    original_logs = preprocess.logs

                    # create graph
                    g = CreateGraph(events_unique)
                    g.do_create()
                    graph = g.g

                    # run improved MajorClust
                    imc = ImprovedMajorClust(graph)
                    clusters = imc.get_improved_majorclust()

                    # get internal evaluation
                    # convert clustering result from graph to text
                    new_clusters = EvaluationUtility.convert_to_text(graph, clusters)
                    internal_evaluation = self.__get_internal_evaluation(new_clusters, preprocessed_logs, log_length)
                    print filename, internal_evaluation

                    # write experiment result and close evaluation file
                    row = (filename, ) + internal_evaluation
                    writer.writerow(row)
                    graph.clear()

                # write clustering result per cluster to text file
                OutputText.percluster_with_logid(self.files[filename]['percluster_path'], new_clusters, original_logs)

            elif self.method in self.methods['non_graph']:
                clusters, original_logs = {}, []
                preprocessed_logs, log_length = {}, 0

                if self.method == 'LogCluster':
                    # initialization of parameters
                    rsupports = linspace(10, 90, 9)
                    log_file = self.files[filename]['log_path']
                    outlier_file = self.files[filename]['outlier_path']
                    output_file = self.files[filename]['output_path']
                    evaluation_results = []

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(log_file, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                    # run LogCluster clustering
                    lc = LogCluster(None, None, log_file, rsupports, outlier_file, output_file)
                    clusters_list = lc.get_clusters_manysupports()
                    for clusters in clusters_list:
                        evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                        evaluation_results.append([evaluation[0], clusters])

                    # choose the best evaluation
                    sorted_value = sorted(evaluation_results, key=itemgetter(0), reverse=True)
                    clusters = sorted_value[0][1]

                elif self.method == 'IPLoM':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = ParaIPLoM(path=dataset_path + '/', logname=filename,
                                     save_path=self.configuration['experiment_result_path']['result_path'])

                    # run IPLoM clustering
                    myiplom = IPLoM(para)
                    myiplom.main_process()
                    clusters = myiplom.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                elif self.method == 'LogSig':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = Para(path=dataset_path + '/', logname=filename,
                                savePath=self.configuration['experiment_result_path']['result_path'],
                                groupNum=3)     # check again about groupNum parameter

                    # run LogSig clustering
                    ls = LogSig(para)
                    ls.mainProcess()
                    clusters = ls.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                elif self.method == 'LKE':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = ParaLKE(path=dataset_path + '/', logname=filename, threshold2=5,
                                   save_path=self.configuration['experiment_result_path']['result_path'])

                    # run LKE clustering
                    lke = LKE(para)
                    lke.main_process()
                    clusters = lke.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(properties['log_path'], False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length
                    original_logs = pp.logs

                # get internal evaluation
                internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                row = (filename, ) + internal_evaluation
                writer.writerow(row)
                print filename, internal_evaluation

                # write clustering result per cluster to text file
                OutputText.percluster_with_logid(self.files[filename]['percluster_path'], clusters, original_logs)

        f.close()


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    # https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class NoDaemonProcessPool(multiprocessing.pool.Pool):
    # We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
    # because the latter is only a wrapper function, not a proper class.
    def __reduce__(self):
        pass

    Process = NoDaemonProcess


# change the method in ClusteringExperiment() to run an experiment.
# change the config file to change the dataset used in experiment.
start = time()
e = ClusteringExperiment('LogCluster')
e.run_clustering()
# e.run_clustering_experiment()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
