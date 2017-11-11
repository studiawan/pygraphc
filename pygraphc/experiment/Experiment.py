from ConfigParser import SafeConfigParser
import os


class Experiment(object):
    def __init__(self, method):
        self.method = method

    def read_config(self):
        parser = SafeConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', self.method + '.conf')
        parser.read(config_path)

        print parser.get('main', 'method')


e = Experiment('EMCSA')
e.read_config()
