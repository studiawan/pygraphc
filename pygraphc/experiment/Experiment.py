from ConfigParser import SafeConfigParser
import os
import fnmatch
# import csv


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

        result_path = self.configuration['experiment_result_path']['result_path']
        for full_path, filename in matches:
            self.files[filename] = {
                'result_path': result_path,
                'log_path': full_path
            }

        if self.configuration['main']['clustering']:
            for full_path, filename in matches:
                # get evaluation file for clustering
                self.files[filename]['evaluation_file'] = \
                    os.path.join(result_path, dataset, self.configuration['clustering_evaluation']['evaluation_file'])

                # get all files for clustering
                properties = {}
                for key, value in self.configuration['clustering_result_path'].iteritems():
                    properties[key] = os.path.join(result_path, dataset, value, filename)

                # update self.files dictionaries
                self.files[filename].update(properties)

        for k, v in self.files.iteritems():
            print k, v

    def __get_methods(self):
        parser = SafeConfigParser()
        current_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(current_path, 'config', 'method.conf')
        parser.read(config_path)

        for section_name in parser.sections():
            options = {}
            methods = []
            for name, value in parser.items(section_name):
                options[name] = value
                methods = options[name].split('\n')
            self.methods[section_name] = methods

    def run_experiment(self):
        self.__get_methods()
        self.__read_config()
        self.__get_dataset()

        # # open evaluation file
        # f = open(self.files['evaluation_file'], 'wt')
        # writer = csv.writer(f)
        #
        # # set header for evaluation file
        # header = self.configuration['clustering_evaluation']['evaluation_file_header']
        # writer.writerow(header)
        #
        # f.close()


e = Experiment('max_clique_weighted_sa')
e.run_experiment()
