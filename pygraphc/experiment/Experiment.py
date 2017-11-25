import os
import errno
import fnmatch
import csv
from time import time
from ConfigParser import SafeConfigParser
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.preprocess.ParallelPreprocess import ParallelPreprocess
from pygraphc.preprocess.PreprocessLog import PreprocessLog
from pygraphc.preprocess.CreateGraph import CreateGraph
from pygraphc.clustering.MaxCliquesPercolationSA import MaxCliquesPercolationSA
from pygraphc.clustering.MajorClust import ImprovedMajorClust
from pygraphc.evaluation.EvaluationUtility import EvaluationUtility
from pygraphc.evaluation.CalinskiHarabaszIndex import CalinskiHarabaszIndex
from pygraphc.evaluation.DaviesBouldinIndex import DaviesBouldinIndex
from pygraphc.evaluation.XieBeniIndex import XieBeniIndex
from pygraphc.misc.ReverseVaarandi import ReverseVaarandi
from pygraphc.misc.IPLoM import ParaIPLoM, IPLoM
from pygraphc.misc.LogSig import Para, LogSig
from pygraphc.misc.DBSCANClustering import DBSCANClustering


class Experiment(object):
    def __init__(self, method):
        self.method = method
        self.configuration = {}
        self.methods = {}
        self.files = {}

    def __read_config(self):
        # read configuration file to run an experiment based on a specific method and a dataset
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', self.method + '.conf')
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

        if self.configuration['main']['clustering']:
            for full_path, filename in matches:
                # get all files for clustering
                properties = {}
                for key, value in self.configuration['clustering_result_path'].iteritems():
                    properties[key] = os.path.join(result_path, dataset, value, filename)
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
        config_path = os.path.join(current_path, 'config', 'method.conf')
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
        if self.configuration['internal_evaluation']['calinski_harabasz']:
            ch = CalinskiHarabaszIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(ch.get_calinski_harabasz())
        if self.configuration['internal_evaluation']['davies_bouldin']:
            db = DaviesBouldinIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(db.get_davies_bouldin())
        if self.configuration['internal_evaluation']['xie_beni']:
            xb = XieBeniIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(xb.get_xie_beni())

        print internal_evaluation
        return tuple(internal_evaluation)

    @staticmethod
    def __check_path(path):
        # check a path is exist or not. if not exist, then create it
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

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

            print filename, '...'
            if self.method in self.methods['graph']:

                if self.method == 'max_clique_weighted_sa':
                    # preprocess log file and create graph
                    preprocess = CreateGraphModel(properties['log_path'])
                    graph = preprocess.create_graph()
                    edges_weight = preprocess.edges_weight
                    nodes_id = range(preprocess.unique_events_length)
                    preprocessed_logs = preprocess.preprocessed_logs
                    log_length = preprocess.log_length

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

                    # write experiment result and close evaluation file
                    row = (filename, best_parameter['k'], best_parameter['I']) + internal_evaluation
                    writer.writerow(row)
                    graph.clear()

                elif self.method == 'improved_majorclust':
                    # preprocess log file
                    # log_type = self.configuration[self.configuration['main']['dataset']]['log_type']
                    log_type = 'auth'
                    preprocess = PreprocessLog(log_type, properties['log_path'])
                    if log_type == 'auth':
                        preprocess.do_preprocess()  # auth

                    events_unique = preprocess.events_unique
                    log_length = preprocess.loglength
                    preprocessed_logs = preprocess.preprocessed_logs

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

                    # write experiment result and close evaluation file
                    row = (filename, ) + internal_evaluation
                    writer.writerow(row)
                    graph.clear()

            elif self.method in self.methods['']:
                if self.method == 'LogCluster' or self.method == 'SLCT':
                    # initialization of parameters
                    mode = self.method
                    support = 100
                    log_file = filename
                    outlier_file = ''
                    output_file = ''

                    # run LogCluster clustering
                    lc = ReverseVaarandi(mode, support, log_file, outlier_file, output_file)
                    clusters = lc.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(log_file, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length

                    # get internal evaluation
                    internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                    row = (filename, ) + internal_evaluation
                    writer.writerow(row)

                elif self.method == 'IPLoM':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = ParaIPLoM(path=dataset_path + '/', logname=filename,
                                     save_path=self.configuration['experiment_result_path']['path'])

                    # run IPLoM clustering
                    myiplom = IPLoM(para)
                    myiplom.main_process()
                    clusters = myiplom.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(filename, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length

                    # get internal evaluation
                    internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                    row = (filename,) + internal_evaluation
                    writer.writerow(row)

                elif self.method == 'LogSig':
                    # set path
                    dataset = self.configuration['main']['dataset']
                    dataset_path = self.configuration[dataset]['path']
                    para = Para(path=dataset_path + '/', logname=filename,
                                savePath=self.configuration['experiment_result_path']['path'],
                                groupNum=3)     # check again about groupNum parameter

                    # run LogSig clustering
                    ls = LogSig(para)
                    ls.mainProcess()
                    clusters = ls.get_clusters()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(filename, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length

                    # get internal evaluation
                    internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                    row = (filename,) + internal_evaluation
                    writer.writerow(row)

                elif self.method == 'DBSCAN':
                    # run DBSCAN clustering
                    db = DBSCANClustering(filename)
                    clusters = db.get_cluster()

                    # preprocess logs for evaluation
                    pp = ParallelPreprocess(filename, False)
                    pp.get_unique_events()
                    preprocessed_logs = pp.preprocessed_logs
                    log_length = pp.log_length

                    # get internal evaluation
                    internal_evaluation = self.__get_internal_evaluation(clusters, preprocessed_logs, log_length)
                    row = (filename,) + internal_evaluation
                    writer.writerow(row)

        f.close()


start = time()
e = Experiment('improved_majorclust')
e.run_clustering_experiment()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
