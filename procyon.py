#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See README.md for information and such.

from procyon import evaluate, evaluate_command
from procyon.common import *  # Exceptions

import sys
import re
import glob
from stat import S_ISDIR
import os
from os import _exit

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
    except (IOError, OSError) as e:
        print("Unable to read file: {}".format(e))
        return None

def complete(text, state):
    """ Custom readline completion function for .import commands. """

    def append_slash(f):
        """ Add a slash to the end of directory names. """
        if S_ISDIR(os.stat(f).st_mode):
            return f + "/"
        else:
            return f

    line = readline.get_line_buffer()

    # If we're not importing, do not tab complete.
    # Attempt to simply insert a tab instead, for indentation.
    if not re.match(r'^\s*\.import\s', line):
        text = "" if re.match("^\s*$", text) else text
        return [text + "\t", None][state]

    # Grab a list of all relevant files, add slashes if they're directories,
    # and append the None so that readline knows when to stop calling us.
    text = os.path.expanduser(text)  # expand ~
    files = glob.glob(text + '*')
    files = [append_slash(f) for f in files]
    files.append(None)
    return files[state]

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

if not filename:
    # REPL; set up readline
    import readline
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(complete)

program = ""
keep_going = False  # used in the REPL; when set, we read another line as a continuation line
last_result = None

filetype = "repl"
if filename:
    filetype = "arg"

#
# I'm not at all happy with the mess this loop has become; one goal
# of this project is to keep the code fairly easy to understand.
# This loop is written in part by trial and error, at this point.
#
# A brief explanation:
# filetype is set to "arg" when reading a file (procyon file.pr), "repl" most of the time
# otherwise, and "import" when executing an .import statement in the REPL.
#
# "import" is only used until the file has loaded successfully, at which point
# filetype is reset to "repl" again. When no exception occurs, this happens
# virtually immediately.

while True:
    if filetype != "arg" and filename:
        # Ugly. When importing a file, we set filename, so that it can be displayed
        # for syntax errors and such. However, we need to unset it again after all exception
        # handlers have run, to clean the state and return to "REPL input mode", so to speak.
        filename = None

    try:
        if filetype == "arg":
            # This is a file passed as an argument to the interpreter
            assert filename is not None
            program = read_file(filename)
            if program is None:
                _exit(1)
        else:
            # This is an interactive REPL session
            filetype = "repl"

            try:
                PROMPT = ">>> "
                CONT_PROMPT = '... '
                if keep_going:
                    # keep_going is set when the input from the previous line(s) is incomplete,
                    # e.g. "print(1, 2," was entered; the user can then enter the rest on one
                    # or more upcoming lines.
                    program += "\n" + input(CONT_PROMPT).strip()
                else:
                    program = input(PROMPT).strip()
            except KeyboardInterrupt:
                print("^C")
                keep_going = False
                program = None
                continue
            except EOFError:
                print("^D")
                _exit(0)

        results = None

        if filename is None and len(program) > 0 and program[0] == '.':
            # Support commands in the REPL only (filename is None)
            if re.match(r'^\s*\.import\s+\S', program):
                # .import is handled here, so that we can re-use the code
                # for pointing out syntax errors and such.
                filename = re.split('\s+', program)[1]
                program = read_file(filename)
                if program is None:
                    filename = None
                    continue

                filetype = "import"
                evaluate(program)

                # If we get here, the evaluation was successful, so clean up
                # prior to looping again
                filetype = "repl"
                filename = None
                program = None
            else:
                evaluate_command(program[1:])

            continue

        elif filename is None:
            # Save results for the REPL...
            results = evaluate(program, last=last_result)
            if results:
                last_result = results[-1]

            keep_going = False
        elif filetype == "arg":
            # ... but not for interpreted files.
            evaluate(program)
            _exit(0)

        if results is not None and len([r for r in results if r is not None]) > 0:
            print("\n".join([str(r) for r in results if r is not None]))

    except ProcyonSyntaxError as e:
        (lineno, pos, ex_msg) = e.args[0]
        keep_going = False

        if lineno > 0 and pos > 0:
            line = program.split('\n')[lineno-1]
            print_error_pos(line, pos)
            print("Syntax error: {} at {}:{}:{}".format(
                ex_msg, filename if filename else "<repl>", lineno, pos))
        else:
            # This was an "unexpected end of input" error.
            # In case this happened in the REPL (filename is None),
            # the user might want to keep typing, so let's let them.
            if filename is None:
                keep_going = True
                continue
            else:
                print("Syntax error: {}: {}".format(filename, ex_msg))

    except ProcyonInternalError as e:
        print("BUG:", str(e))
        _exit(1)
    except ProcyonControlFlowException as e:
        keep_going = False
        t = e.args[0]["type"]
        if t == "abort":
            print("abort() called")
        else:
            print("Error: {} called outside of a {}".format(
                t, "function" if t == "return" else "loop"))
    except ProcyonNameError as e:
        keep_going = False
        print("Name error: {}".format(str(e)))
    except OverflowError:
        keep_going = False
        print("Overflow: result is out of range")
    except ProcyonTypeError as e:
        keep_going = False
        print("Type error: {}".format(str(e)))
    finally:
        if filename and filetype == "arg":
            # If we get here, an exception was raised, or else
            # we would have exited with status 0 previously.
            sys.exit(1)
