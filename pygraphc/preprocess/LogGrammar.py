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
        if self.log_type == 'auth':
            self.authlog_grammar = self.__get_authlog_grammar()
        elif self.log_type == 'kippo':
            self.kippolog_grammar = self.__get_kippolog_grammar()
        elif self.log_type == 'syslog':
            self.syslog_grammar = self.__get_syslog_grammar()
        elif self.log_type == 'bluegene':
            self.bluegene_grammar = self.__get_bluegene_grammar()
        elif self.log_type == 'raslog':
            self.raslog_grammar = self.__get_raslog_grammar()

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
        """The definition of syslog grammar.

        Returns
        -------
        syslog_grammar    :
            Grammar for syslog.
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
        message = Optional(Suppress(": [") + Word(nums + '.') + Suppress("]")) + Regex(".*")
        
        syslog_grammar = timestamp + hostname + appname + message
        return syslog_grammar

    def parse_syslog(self, log_line):
        """Parse syslog based on defined grammar.

        Parameters
        ----------
        log_line    : str
            A log line to be parsed.

        Returns
        -------
        parsed      : dict[str, str]
            A parsed syslog (or messages in RedHat-based Linux) containing these elements:
            timestamp, hostname, service, message, time in second (optional), and pid (optional).
        """
        parsed_syslog = self.syslog_grammar.parseString(log_line)

        parsed = dict()
        parsed['timestamp'] = parsed_syslog[0] + ' ' + parsed_syslog[1] + ' ' + parsed_syslog[2]
        parsed['hostname'] = parsed_syslog[3]
        parsed['service'] = parsed_syslog[4]
        if '.' in parsed_syslog[5]:
            parsed['second'] = parsed_syslog[5]
        else:
            parsed['pid'] = parsed_syslog[5]
        parsed['message'] = parsed_syslog[6]

        return parsed

    @staticmethod
    def __get_bluegene_grammar():
        """The definition of BlueGene/L grammar.

        The BlueGene/L logs can be downloaded from [Useninx2006a]_ and
        this data was used in [Stearley2008]_.

        Returns
        -------
        bluegene_grammar    :
            Grammar for BlueGene/L supercomputer logs.

        References
        ----------
        .. [Usenix2006a]  The HPC4 data. URL: https://www.usenix.org/cfdr-data#hpc4
        .. [Stearley2008] Stearley, J., & Oliner, A. J. Bad words: Finding faults in Spirit's syslogs.
                          In 8th IEEE International Symposium on Cluster Computing and the Grid, pp. 765-770.
        """
        ints = Word(nums)

        sock = Word(alphas + '-')
        number = ints
        date = Combine(ints + '.' + ints + '.' + ints)
        core1 = Word(alphas + nums + "-" + ":")
        datetime = Combine(ints + '-' + ints + '-' + ints + '-' + ints + '.' + ints + '.' + ints + '.' + ints)
        core2 = Word(alphas + nums + "-" + ":")
        source = Word(alphas)
        service = Word(alphas)
        info_type = Word(alphas)
        message = Regex('.*')

        # blue gene log grammar
        bluegene_grammar = sock + number + date + core1 + datetime + core2 + source + service + info_type + message
        return bluegene_grammar

    def parse_bluegenelog(self, log_line):
        """Parse the BlueGene/L logs based on defined grammar.

        Parameters
        ----------
        log_line    : str
            A log line to be parsed

        Returns
        -------
        parsed      : dict[str, str]
            A parsed BlueGene/L log.
        """
        parsed_bluegenelog = self.bluegene_grammar.parseString(log_line)

        parsed = dict()
        parsed['sock'] = parsed_bluegenelog[0]
        parsed['number'] = parsed_bluegenelog[1]
        parsed['date'] = parsed_bluegenelog[2]
        parsed['core1'] = parsed_bluegenelog[3]
        parsed['timestamp'] = parsed_bluegenelog[4]
        parsed['core2'] = parsed_bluegenelog[5]
        parsed['source'] = parsed_bluegenelog[6]
        parsed['service'] = parsed_bluegenelog[7]
        parsed['info_type'] = parsed_bluegenelog[8]
        parsed['message'] = parsed_bluegenelog[9]

        return parsed

    @staticmethod
    def __get_raslog_grammar():
        """The definition of RAS log grammar.

        The BlueGene/P RAS logs can be downloaded from [Useninx2009a]_
        this data was used in [Zheng2011]_.

        Returns
        -------
        bluegene_grammar    :
            Grammar for BlueGene/P RAS supercomputer logs.

        References
        ----------
        .. [Usenix2009a] Blue Gene/P data from Intrepid. URL: https://www.usenix.org/cfdr-data
        .. [Zheng2011]   Z. Zheng, L. Yu, W. Tang, Z. Lan, R. Gupta, N. Desai, S. Coghlan, and D. Buettner,
                         Co-Analysis of RAS Log and Job Log on Blue Gene/P, in Proc. of IEEE International Parallel &
                         Distributed Processing Symposium, 2011.
        """
        ints = Word(nums)

        recid = ints
        msg_id = Word(alphas + nums + '_')
        component = Word(alphas)
        subcomponent = Word(alphas + nums + '_')
        errcode = Word(alphas + nums + '_')
        severity = Word(alphas)
        timestamp = Combine(ints + '-' + ints + '-' + ints + '-' + ints + '.' + ints + '.' + ints + '.' + ints)
        flags = Word(nums + '-')
        processor = Word(nums + '-')
        node = Word(nums + '-')
        block = Word(alphas + nums + '-' + '_')
        location = Word(alphas + nums + '-')
        serialnumber = Word(alphas + nums)
        ecid = Word(alphas + nums + "'")
        message = Regex('.*')

        raslog_grammar = recid + msg_id + component + subcomponent + errcode + severity + timestamp + flags + \
            processor + node + block + location + serialnumber + ecid + message
        return raslog_grammar

    def parse_raslog(self, log_line):
        """Parse the RAS logs based on defined grammar.

        Parameters
        ----------
        log_line    : str
            A log line to be parsed

        Returns
        -------
        parsed      : dict[str, str]
            A parsed RAS log.
        """
        parsed_raslog = self.raslog_grammar.parseString(log_line)

        parsed = dict()
        parsed['recid'] = parsed_raslog[0]
        parsed['msg_id'] = parsed_raslog[1]
        parsed['component'] = parsed_raslog[2]
        parsed['subcomponent'] = parsed_raslog[3]
        parsed['errcode'] = parsed_raslog[4]
        parsed['severity'] = parsed_raslog[5]
        parsed['timestamp'] = parsed_raslog[6]
        parsed['flags'] = parsed_raslog[7]
        parsed['processor'] = parsed_raslog[8]
        parsed['node'] = parsed_raslog[9]
        parsed['block'] = parsed_raslog[10]
        parsed['location'] = parsed_raslog[11]
        parsed['serialnumber'] = parsed_raslog[12]
        parsed['ecid'] = parsed_raslog[13]
        parsed['message'] = parsed_raslog[14]

        return parsed
