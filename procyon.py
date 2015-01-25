#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See README.md for information and such.

from procyon import evaluate, evaluate_command
from procyon.common import *  # Exceptions

import sys
import re
import readline

def usage():
    print("""Procyon interpreter version {}, {}
Usage: {} <file.pr>""".format(VERSION, DATE, sys.argv[0]), file=sys.stderr)

def print_error_pos(line, pos):
    whitespace = re.sub(r'[^\t]', " ", line[:pos])
    print(line)
    print(whitespace[:-1] + "^")

def read_file(filename):
    """ Read a file, and return its contents. """
    program = None
    try:
        with open(filename, 'r') as f:
            program = f.read()
            return program
    except Exception as e:
        print("Unable to read file: {}".format(e))
        sys.exit(1)

filename = None

if len(sys.argv) == 1:
    # REPL
    print("Procyon interpreter version " + VERSION + ", " + DATE)
elif len(sys.argv) == 2:
    # Interpret a file
    filename = sys.argv[1]
else:
    # Invalid command line
    usage()
    sys.exit(1)

program = None
last_result = None
while True:
    if filename and program:
        # Ugly, but it works.
        # Only run the loop once if interpreting a file.
        # When program is not None, it has already run once.
        # This way, exception handling can be shared between both ways of using the script.
        # If the program ran without exceptions, sys.exit(0) is called, so any time we get here,
        # something should've gone wrong.
        sys.exit(1)
    try:
        if filename is not None:
                program = read_file(filename)
        else:
            try:
                PROMPT = '>>> '
                program = input(PROMPT).strip()
            except (KeyboardInterrupt, EOFError):
                print("")
                sys.exit(0)

        results = None
        if filename is None and len(program) > 0 and program[0] == '.':
            # Support commands in the REPL only (filename is None)
            evaluate_command(program[1:])
            continue
        elif filename is None:
            # Save results for the REPL...
            results = evaluate(program, last=last_result)
            if len(results) > 0:
                last_result = results[-1]
        else:
            # ... but not for interpreted files.
            evaluate(program)
            sys.exit(0)

        if results is not None and len([r for r in results if r is not None]) > 0:
            print("\n".join([str(r) for r in results if r is not None]))

    except ProcyonSyntaxError as e:
        (lineno, pos, ex_msg) = e.args[0]

        if lineno > 0 and pos > 0:
            line = program.split('\n')[lineno-1]
            print_error_pos(line, pos)
            print("Syntax error: {} at {}:{}:{}".format(
                ex_msg, filename if filename else "<repl>", lineno, pos))
        else:
            # If the error is "unexpetced end of input", the above variables will be -1,
            # and there's no use in printing either of them.
            print("Syntax error: {}: {}".format(filename if filename else "<repl>", ex_msg))

    except ProcyonInternalError as e:
        print("BUG:", str(e))
        sys.exit(1)
    except ProcyonControlFlowException as e:
        type = e.args[0]["type"]
        if type == "abort":
            print("abort() called")
        else:
            print("Error: {} called outside of a {}".format(
                type, "function" if type == "return" else "loop"))
    except ProcyonNameError as e:
        print("Name error: {}".format(str(e)))
    except OverflowError:
        print("Overflow: result is out of range")
    except ProcyonTypeError as e:
        print("Type error: {}".format(str(e)))
    except Exception as e:
        print(str(e))
