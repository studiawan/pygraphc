from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex


class LogGrammar(object):
    def __init__(self, log_line):
        self.log_line = log_line
        self.authlog_grammar = None

    def get_authlog_grammar(self):
        ints = Word(nums)

        # timestamp
        month = Word(string.uppercase, string.lowercase, exact=3)
        day = ints
        hour = Combine(ints + ":" + ints + ":" + ints)
        timestamp = month + day + hour

        # hostname, service name, message
        hostname = Word(alphas + nums + "_" + "-" + ".")
        appname = Word(alphas + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")
        message = Regex(".*")

        # auth log grammar
        self.authlog_grammar = timestamp + hostname + appname + message

    def parse_authlog(self):
        parsed = {}
        parsed_authlog = self.authlog_grammar.parseString(self.log_line)

        parsed['timestamp'] = parsed_authlog[0] + ' ' + parsed_authlog[1] + ' ' + parsed_authlog[2]
        parsed['hostname'] = parsed_authlog[3]
        parsed['service'] = parsed_authlog[4]
        parsed['pid'] = parsed_authlog[5]
        parsed['message'] = parsed_authlog[6]

        return parsed
