from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex


class LogGrammar(object):
    """A class to define the format (grammar) of a log file.

    We heavily rely on pyparsing in this case. The code for auth.log grammar is derived from syslog parser
    by L. Silva [Silva2012]_.

    References
    ----------
    .. [Silva2012] L. Silva, Parsing syslog files with Python and PyParsing, 2012.
                   https://gist.github.com/leandrosilva/3651640
    """
    def __init__(self, log_type=None):
        """The constructor of LogGrammar.
        """
        self.log_type = log_type
        self.authlog_grammar = self.__get_authlog_grammar()
        self.kippolog_grammar = self.__get_kippolog_grammar()

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
        hostname_or_ip = Word(alphas + nums + "_" + "-" + ".")
        appname = Word(alphas + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")
        message = Regex(".*")

        # auth log grammar
        authlog_grammar = timestamp + hostname_or_ip + appname + message
        return authlog_grammar

    def parse_authlog(self, log_line):
        """Parse auth.log based on defined grammar.

        Returns
        -------
        parsed  : dict[str, str]
            A parsed auth.log containing these elements: timestamp, hostname, service, pid, and message.
        """
        parsed_authlog = self.authlog_grammar.parseString(log_line)

        # get parsed auth.log
        parsed = dict()
        parsed['timestamp'] = parsed_authlog[0] + ' ' + parsed_authlog[1] + ' ' + parsed_authlog[2]
        if self.log_type == 'Hofstede2014':
            parsed['ip_address'] = parsed_authlog[3]
        else:
            parsed['hostname'] = parsed_authlog[3]

        parsed['service'] = parsed_authlog[4]

        if len(parsed_authlog) < 7:
            parsed['message'] = parsed_authlog[5]
        else:
            parsed['pid'] = parsed_authlog[5]
            parsed['message'] = parsed_authlog[6]

        return parsed

    @staticmethod
    def __get_kippolog_grammar():
        ints = Word(nums)

        # date and time
        date = Combine(ints + '-' + ints + '-' + ints)
        time = Combine(ints + ':' + ints + ':' + ints + '+0000')
        datetime = date + time

        # service = activity, port, and ip address
        ip_address = Word(nums + '.')
        activity = Word(alphas + nums + '-' + ' ') + Optional(Suppress(',') + ints + Suppress(',') + ip_address)
        service = Suppress('[') + activity + Suppress(']')

        # message
        message = Regex(".*")

        # kippo honeypot log grammar
        kippolog_grammar = datetime + service + message
        return kippolog_grammar

    def parse_kipplog(self, log_line):
        parsed_kippolog = self.kippolog_grammar.parseString(log_line)
        parsed = dict()
        parsed['timestamp'] = parsed_kippolog[0] + ' ' + parsed_kippolog[1]
        if len(parsed_kippolog) < 5:
            parsed['service'] = parsed_kippolog[2]
            parsed['message'] = parsed_kippolog[3]
        else:
            parsed['service'] = parsed_kippolog[2]
            parsed['port'] = parsed_kippolog[3]
            parsed['ip_address'] = parsed_kippolog[4]
            parsed['message'] = parsed_kippolog[5]

        return parsed
