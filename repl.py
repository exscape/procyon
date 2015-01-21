#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See README.md for information and such.

from procyon import evaluate, evaluate_command
from procyon.common import *  # VERSION, DATE and exceptions

import sys
import readline
import re

PROMPT = '>>> '

def print_error_pos(line, pos):
    assert line == 1
    print(" " * (pos - 1 + len(PROMPT)) + "^")

print("Procyon interpreter v" + VERSION + ", " + DATE)

while True:
    try:
        input_str = input(PROMPT).strip()
        try:
            if len(input_str) > 0 and input_str[0] == '.':
                if len(input_str.split()) > 1:
                    print('Invalid command:', input_str)
                else:
                    evaluate_command(input_str[1:])
                continue
            else:
                results = evaluate(input_str)

            if results is not None and len([r for r in results if r is not None]) > 0:
                print("\n".join([str(r) for r in results if r is not None]))
        except ProcyonNameError as e:
            print("Name error: {}".format(str(e)))
        except OverflowError:
            print("Overflow: result is out of range")
        except ProcyonSyntaxError as e:
            (line, pos, ex_msg) = e.args[0]
            if line > 0 and pos > 0:
                print_error_pos(line, pos)
                print("Syntax error: {} at input position {}:{}".format(ex_msg, line, pos))
            else:
                print("Syntax error: {}".format(ex_msg))
        except ProcyonTypeError as e:
            print("Type error: {}".format(str(e)))
        except ProcyonInternalError as e:
            print("BUG: {}".format(str(e)))
            sys.exit(1)

    except (KeyboardInterrupt, EOFError):
        print("")
        sys.exit(0)
