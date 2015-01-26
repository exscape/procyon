# vim: ts=4 sts=4 et sw=4

# Minor stuff that is shared by various modules is stored here.

import re
import codecs

VERSION = '0.16a'
DATE = '2015-01-27'
DEBUGPARSE = 0

class ProcyonException(Exception):
    """ Base exception for all Procyon exceptions.

        Where applicable, exceptions have two arguments, and are created
        like so: raise ProcyonNameError((line, col), "Message")
    """

class ProcyonSyntaxError(ProcyonException):
    """ Raised when the lexer/parser detects a syntax error. """
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

class ProcyonControlFlowException(ProcyonException):
    """ Raised by return, break, continue and abort(); exception arguments show the type.

        args[0] is a dictionary with one or two entries.
        "type": "return" | "break" | "continue" | "abort", and if type is "return",
        also a key named "value" holding the function's return value.
    """
    pass

def decode_escapes(s):
    r""" Handle escape sequences in strings.

         On a basic level, this allows for \n to mean newline and so on, but
         it does encompass more.
         Code from: http://stackoverflow.com/a/24519338/1668576
    """

    if type(s) is not str:
        return s

    ESCAPE_SEQUENCE_RE = re.compile(r'''
        ( \\U........      # 8-digit hex escapes
        | \\u....          # 4-digit hex escapes
        | \\x..            # 2-digit hex escapes
        | \\[0-7]{1,3}     # Octal escapes
        | \\N\{[^}]+\}     # Unicode characters by name
        | \\[\\'"abfnrtv]  # Single-character escapes
        )''', re.UNICODE | re.VERBOSE)

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)
