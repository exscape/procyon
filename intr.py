#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See README.md for information and such.

from procyon import evaluate_file
from procyon.common import *  # Exceptions

import sys
import re
import readline

def usage():
    print(""" Procyon interpreter.
Usage: {} <file.pr>""".format(sys.argv[0]), file=sys.stderr)

def read_file(filename):
    """ Read a file. The caller is responsible for handling exceptions. """
    program = None
    with open(filename, 'r') as f:
        program = f.read()
        return program

if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        sys.exit(1)
    filename = sys.argv[1]

    try:
        evaluate_file(filename)
        sys.exit(0)
    except ProcyonSyntaxError as e:
        (line, pos, ex_msg) = e.args[0]
        program = None
        try:
            program = read_file(filename)
        except Exception as e:
            # This seems unlikely since the read succeeded just previously,
            # but simply not checking doesn't seem right.
            print("Unable to re-read file after catching syntax error! {}".format(e))
            sys.exit(1)

        if line > 0 and pos > 0:
            prog_line = program.split('\n')[line-1]
            print(prog_line)
            print(" " * (pos - 1) + "^")
            print("Syntax error: {} at {}:{}:{}".format(ex_msg, filename, line, pos))
        else:
            # If the error is "unexpected end of input", the position is not printed, and so
            # the regex doesn't match.
            print("Syntax error: {}: {}".format(filename, ex_msg))

    except ProcyonInternalError as e:
        print(str(e))
        sys.exit(1)
    except ProcyonNameError as e:
        print("Name error: {}".format(str(e)))
    except OverflowError:
        print("Overflow: result is out of range")
    except ProcyonTypeError as e:
        print("Type error: {}".format(str(e)))
    except Exception as e:
        print(str(e))

    sys.exit(1)
