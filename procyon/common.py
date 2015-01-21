# vim: ts=4 sts=4 et sw=4

# Minor stuff that is shared by various modules is stored here.

VERSION = '0.14a'
DATE = '2015-01-21'
DEBUGPARSE = 0

class ProcyonException(Exception):
    """ Base exception for all Procyon exceptions. """

class ProcyonSyntaxError(ProcyonException):
    """ Raised when the lexer/parser detects a syntax error.

        The exception message contains the line and column number where the error
        was detected, in the format line:column (both counting from 1).
    """
    pass

class ProcyonInternalError(ProcyonException):
    """ Raised when an interpreter bug occurs, such as when encountering unknown AST nodes. """
    pass

class ProcyonNameError(ProcyonException):
    """ Raised when the interpreter encounters an unknown variable or function name. """
    pass


class ProcyonTypeError(ProcyonException):
    """ Raised when the interpreter encounters a type error, such as adding an int to a string. """
    pass

class ProcyonReturnException(ProcyonException):
    """ Raised when a function returns, with its return value as the exception value. """
    pass
