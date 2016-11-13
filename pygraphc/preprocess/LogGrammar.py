from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex


class LogGrammar(object):
    """A class to define the format (grammar) of a log file. We heavily rely on pyparsing in this case.
    """
    def __init__(self, log_line):
        """The constructor of LogGrammar.

        Parameters
        ----------
        log_line    : str
            A log line to be parsed.
        """
        self.log_line = log_line

    @staticmethod
    def __get_authlog_grammar():
        """The definition of auth.log grammar.
        """
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
        authlog_grammar = timestamp + hostname + appname + message
        return authlog_grammar

    def parse_authlog(self):
        """Parse auth.log based on defined grammar.

        Returns
        -------
        parsed  : dict[str, str]
            A parsed auth.log containing these elements: timestamp, hostname, service, pid, and message.
        """
        # get auth.log grammar
        authlog_grammar = self.__get_authlog_grammar()
        parsed_authlog = authlog_grammar.parseString(self.log_line)

        # get parsed auth.log
        parsed = dict()
        parsed['timestamp'] = parsed_authlog[0] + ' ' + parsed_authlog[1] + ' ' + parsed_authlog[2]
        parsed['hostname'] = parsed_authlog[3]
        parsed['service'] = parsed_authlog[4]
        parsed['pid'] = parsed_authlog[5]
        parsed['message'] = parsed_authlog[6]

        return parsed
