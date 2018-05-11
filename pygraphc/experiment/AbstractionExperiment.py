import os
import errno
import csv
import multiprocessing
import multiprocessing.pool
from time import time
from ConfigParser import SafeConfigParser
from pygraphc.abstraction.AutoAbstraction import AutoAbstraction
from pygraphc.abstraction.AbstractionUtility import AbstractionUtility
from pygraphc.evaluation.ExternalEvaluation import ExternalEvaluation


class AbstractionExperiment(object):
    def __init__(self, method):
        self.method = method
        self.configuration = {}
        self.dataset_configuration = {}
        self.methods = {}
        self.files = {}

    def __read_config(self):
        # read configuration file to run an experiment based on a specific method and a dataset
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', 'abstraction', self.method + '.conf')
        parser.read(config_path)

        for section_name in parser.sections():
            options = {}
            for name, value in parser.items(section_name):
                options[name] = value
            self.configuration[section_name] = options

    def __get_dataset(self):
        # get all log files under dataset directory
        dataset = self.configuration['main']['dataset']
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        dataset_config_path = os.path.join(current_path, 'config', 'abstraction', 'datasets.conf')
        parser.read(dataset_config_path)

        # read dataset section
        for section_name in parser.sections():
            options = {}
            for name, value in parser.items(section_name):
                options[name] = value
            self.dataset_configuration[section_name] = options

        # get full path of each filename
        dataset_path = self.dataset_configuration['main']['dataset_path']
        dataset_path_logs = os.path.join(self.dataset_configuration['main']['dataset_path'], dataset,
                                         self.dataset_configuration['main']['logs_path'])
        matches = []
        for root, dirnames, filenames in os.walk(dataset_path_logs):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                matches.append((full_path, filename))

        # set experiment result path and a single log file path
        result_path = self.configuration['experiment_result_path']['result_path']
        for full_path, filename in matches:
            self.files[filename] = {
                'result_path': result_path,
                'log_path': full_path
            }

        if self.configuration['main']['abstraction'] == '1':
            for full_path, filename in matches:
                # get all files for abstraction
                properties = {}
                for key, value in self.configuration['abstraction_result_path'].iteritems():
                    directory = os.path.join(result_path, dataset, value)
                    self.__check_path(directory)
                    properties[key] = os.path.join(directory, filename)

                # update files dictionary
                self.files[filename].update(properties)

                # get ground truth for each file
                properties = {}
                for key, value in self.configuration['abstraction_ground_truth'].iteritems():
                    properties[key] = os.path.join(dataset_path, dataset, value, filename)

                # update files dictionary
                self.files[filename].update(properties)

            # get evaluation directory and file for clustering
            self.files['evaluation_directory'] = \
                os.path.join(result_path, dataset,
                             self.configuration['abstraction_evaluation']['evaluation_directory'])
            self.files['evaluation_file'] = \
                os.path.join(result_path, dataset,
                             self.configuration['abstraction_evaluation']['evaluation_directory'],
                             self.configuration['abstraction_evaluation']['evaluation_file'])

    @staticmethod
    def __check_path(path):
        # check a path is exist or not. if not exist, then create it
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def __get_methods(self):
        # get all of available methods from config file
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', 'abstraction', 'method.conf')
        parser.read(config_path)

        for section_name in parser.sections():
            options, methods = {}, []
            for name, value in parser.items(section_name):
                options[name] = value
                methods = options[name].split('\n')
            self.methods[section_name] = methods

    def __get_external_evaluation(self, standard_file, prediction_file):
        external_evaluation = []
        if self.configuration['external_evaluation']['adjusted_rand_index'] == '1':
            ari = ExternalEvaluation.get_adjusted_rand(standard_file, prediction_file, isjson=True, isint=True)
            external_evaluation.append(ari)

        if self.configuration['external_evaluation']['adjusted_mutual_info'] == '1':
            nmi = ExternalEvaluation.get_adjusted_mutual_info(standard_file, prediction_file, isjson=True, isint=True)
            external_evaluation.append(nmi)

        if self.configuration['external_evaluation']['fowlkes_mallows_index'] == '1':
            fms = ExternalEvaluation.get_fowlkes_mallows_score(standard_file, prediction_file, isjson=True, isint=True)
            external_evaluation.append(fms)

        return tuple(external_evaluation)

    @staticmethod
    def __run_alaf(filename):
        auto_abstraction = AutoAbstraction(filename)
        abstractions = auto_abstraction.get_abstraction()

        return abstractions

    def __run_iplom(self):
        pass

    def __run_logsig(self):
        pass

    def __run_lke(self):
        pass

    def __run_logcluster(self):
        pass

    def __run_drain(self):
        pass

    def __get_abstraction(self, filename_properties):
        # run the experiment
        filename = filename_properties[0]
        properties = filename_properties[1]
        row = ()
        abstractions = {}

        if filename != 'evaluation_directory' and filename != 'evaluation_file':
            if self.method in self.methods['graph']:

                if self.method == 'alaf':
                    abstractions = self.__run_alaf(properties['log_path'])

            elif self.method in self.methods['non_graph']:

                if self.method == 'IPLoM':
                    self.__run_iplom()

                elif self.method == 'LogSig':
                    self.__run_logsig()

                elif self.method == 'LKE':
                    self.__run_lke()

                elif self.method == 'LogCluster':
                    self.__run_logcluster()

                elif self.method == 'Drain':
                    self.__run_drain()

            # update abstraction id based on ground truth
            abstractions = \
                AbstractionUtility.get_abstractionid_from_groundtruth(properties['abstraction_label_withid_path'],
                                                                      abstractions)

            # write result to file
            AbstractionUtility.write_perline(abstractions, properties['log_path'], properties['perline_path'])
            AbstractionUtility.write_perabstraction(abstractions, properties['log_path'],
                                                    properties['perabstraction_path'])

            # get external evaluation
            external_evaluation = self.__get_external_evaluation(properties['lineid_abstractionid_path'],
                                                                 properties['perline_path'])
            row = (filename,) + external_evaluation
            print filename, external_evaluation

        return row

    def __call__(self, filename_properties):
        # main method called when running in multiprocessing
        return self.__get_abstraction(filename_properties)

    def run_abstraction_serial(self):
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
        if self.configuration['main']['abstraction'] == '1':
            header = self.configuration['abstraction_evaluation']['evaluation_file_header'].split('\n')
        writer.writerow(tuple(header))

        # run the experiment
        for filename, properties in self.files.iteritems():
            row = self.__get_abstraction((filename, properties))
            writer.writerow(row)

        # close evaluation file
        f.close()

    def run_abstraction_parallel(self):
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
        if self.configuration['main']['abstraction'] == '1':
            header = self.configuration['abstraction_evaluation']['evaluation_file_header'].split('\n')
        writer.writerow(tuple(header))

        # write experiment result
        for result in results:
            writer.writerow(result)

        # close evaluation file
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


# run the experiment
start = time()
abstraction_methods = ['alaf', 'iplom', 'logsig', 'lke', 'logcluster', 'drain']
e = AbstractionExperiment(abstraction_methods[0])
e.run_abstraction_serial()

# print runtime
duration = time() - start
minute, second = divmod(duration, 60)
hour, minute = divmod(minute, 60)
print "Runtime: %d:%02d:%02d" % (hour, minute, second)
