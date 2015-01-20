# vim: ts=4 sts=4 et sw=4

# Minor stuff that is shared by various modules is stored here.

VERSION = '0.14a'
DATE = '2015-01-20'
PROMPT = '>>> '
DEBUGPARSE = 0

class ReturnException(Exception):
    """ Thrown when a function returns, with its return value as the exception value. """
    pass
