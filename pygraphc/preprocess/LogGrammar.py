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
        self.syslog_grammar = self.__get_syslog_grammar()

    @staticmethod
    def __get_authlog_grammar():
        """The definition of auth.log grammar.

        Returns
        -------
        authlog_grammar :
            Grammar for auth.log
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

        Parameters
        ----------
        log_line    : str
            A log line to be parsed.

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
        """The definition of Kippo honeypot log grammar.

        Returns
        -------
        kippolog_grammar    :
            Grammar for Kippo log.
        """
        ints = Word(nums)

        # date and time
        date = Combine(ints + '-' + ints + '-' + ints)
        time = Combine(ints + ':' + ints + ':' + ints + '+0000')
        datetime = date + time

        # service = activity, port, and ip address
        ip_address = Word(nums + '.')
        activity = Word(alphas + nums + '-' + '.' + ' ' + '(' + ')') + Optional(Suppress(',') + ints + Suppress(',') +
                                                                                ip_address)
        service = Suppress('[') + activity + Suppress(']')

        # message
        message = Regex(".*")

        # kippo honeypot log grammar
        kippolog_grammar = datetime + service + message
        return kippolog_grammar

    def parse_kipplog(self, log_line):
        """Parse Kippo log based on defined grammar.

        Parameters
        ----------
        log_line    : str
            A log line to be parsed.

        Returns
        -------
        parsed      : dict[str, str]
            A parsed Kippo honeypot log (kippo.log) containing these elements:
            timestamp, service, message, port (optional), IP address (optional).
        """
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

    @staticmethod
    def __get_syslog_grammar():
        ints = Word(nums)

        # timestamp
        month = Word(string.uppercase, string.lowercase, exact=3)
        day = ints
        hour = Combine(ints + ":" + ints + ":" + ints)
        timestamp = month + day + hour

        # hostname, service name, message
        hostname = Word(alphas + nums + "_" + "-" + ".")
        appname = Word(alphas + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")
        message = Optional(Suppress(": [") + Word(nums + '.') + Suppress("]")) + Regex(".*")
        
        syslog_grammar = timestamp + hostname + appname + message
        return syslog_grammar

    def parse_syslog(self, log_line):
        parsed_syslog = self.syslog_grammar.parseString(log_line)

        parsed = dict()
        parsed['timestamp'] = parsed_syslog[0] + ' ' + parsed_syslog[1] + ' ' + parsed_syslog[2]
        parsed['hostname'] = parsed_syslog[3]
        parsed['service'] = parsed_syslog[4]
        parsed['message'] = parsed_syslog[5]

        return parsed
