from ConfigParser import SafeConfigParser
import os
import fnmatch


class Experiment(object):
    def __init__(self, method):
        self.method = method
        self.configuration = {}

    def __read_config(self):
        # read configuration file to run an experiment based on a specific mathod and a dataset
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

        files = {}
        result_path = self.configuration['experiment_result_path']['result_path']
        for full_path, filename in matches:
            files[filename] = {
                'result_path': result_path,
                'log_path': full_path,
                'result_percluster': result_path + filename + '.percluster',
                'result_perline': result_path + filename + '.perline',
            }

        if self.configuration['main']['clustering']:
            for full_path, filename in matches:
                properties = {}
                for key, value in self.configuration['clustering_result_path']:
                    properties[key] = os.path.join(result_path, filename, value)

                # concat two dictionaries
                files[filename] = {

                }

    def run_experiment(self):
        self.__read_config()
        self.__get_dataset()


e = Experiment('EMCSA')
e.run_experiment()
