import os
import errno
import fnmatch
import csv
from time import time
from ConfigParser import SafeConfigParser
from pygraphc.preprocess.CreateGraphModel import CreateGraphModel
from pygraphc.clustering.MaxCliquesPercolationSA import MaxCliquesPercolationSA
from pygraphc.evaluation.EvaluationUtility import EvaluationUtility
from pygraphc.evaluation.CalinskiHarabaszIndex import CalinskiHarabaszIndex
from pygraphc.evaluation.DaviesBouldinIndex import DaviesBouldinIndex
from pygraphc.evaluation.XieBeniIndex import XieBeniIndex


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
            internal_evaluation.append(ch)
        elif self.configuration['internal_evaluation']['davies_bouldin']:
            db = DaviesBouldinIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(db)
        elif self.configuration['internal_evaluation']['xie_beni']:
            xb = XieBeniIndex(new_clusters, preprocessed_logs, log_length)
            internal_evaluation.append(xb)

        return tuple(internal_evaluation)

    @staticmethod
    def __check_path(path):
        # check a path is exist or not. if not exist, then create it
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def run_experiment(self):
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
        row = ()

        # run the experiment
        for filename, properties in self.files.iteritems():
            print filename, '...'

            if self.method in self.methods['graph']:
                # preprocess log file and create graph
                preprocess = CreateGraphModel(properties['log_path'])
                graph = preprocess.create_graph()
                edges_weight = preprocess.edges_weight
                nodes_id = range(preprocess.unique_events_length)
                preprocessed_logs = preprocess.preprocessed_logs
                log_length = preprocess.log_length

                if self.method == 'max_clique_weighted_sa':
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
                    row = (filename, best_parameter['k'], best_parameter['I']) + internal_evaluation

        # write experiment result and close evaluation file
        writer.writerow(row)
        f.close()


start = time()
e = Experiment('max_clique_weighted_sa')
e.run_experiment()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
