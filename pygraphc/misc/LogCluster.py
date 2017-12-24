import datetime
import hashlib
import textwrap


# This function logs the message given with parameter2,++,parameterN to
# syslog, using the level parameter1+ The message is also written to stderr+
def log_msg(*parameters):
    level = parameters[0]
    msg = ' '.join(parameters[1:])
    now = datetime.datetime.now()
    print now, level, msg


# This function hashes the string given with parameter1 to an integer
# in the range (0+++wsize-1) and returns the integer+ The wsize integer
# can be set with the --wsize command line option+
# L is unsigned 32 bit integer
def hash_string(parameter, wsize):
    wraps = textwrap.wrap(parameter, wsize)
    hashes = []
    for wrap in wraps:
        hash_value = hashlib.md5(wrap).hexdigest()
        hashes.append(int(hash_value, 32))

    return hashes


# This function hashes the candidate ID given with parameter1 to an integer
# in the range (0+++csize-1) and returns the integer+ The csize integer
# can be set with the --csize command line option+
def hash_candidate(parameter, csize):
    wraps = textwrap.wrap(parameter, csize)
    hashes = []
    for wrap in wraps:
        hash_value = hashlib.md5(wrap).hexdigest()
        hashes.append(int(hash_value, 32))

    return hashes


# This function matches the line given with parameter1 with a regular
# expression lineregexp (the expression can be set with the --lfilter
# command line option)+ If the template string is defined (can be set
# with the --template command line option), the line is converted
# according to template (match variables in template are substituted
# with values from regular expression match, and the resulting string
# replaces the line)+ If the regular expression lineregexp does not match
# the line, 0 is returned, otherwise the line (or converted line, if
# --template option has been given) is returned+
# If the --lfilter option has not been given but --lcfunc option is
# present, the Perl function given with --lcfunc is used for matching
# and converting the line+ If the function returns 'undef', line is
# regarded non-matching, otherwise the value returned by the function
# replaces the original line+
# If neither --lfilter nor --lcfunc option has been given, the line
# is returned without a trailing newline+
def process_line():
    pass


# This function makes a pass over the data set and builds the sketch
# @wsketch which is used for finding frequent words+ The sketch contains
# wsize counters (wsize can be set with --wsize command line option)+
def build_word_sketch():
    pass
