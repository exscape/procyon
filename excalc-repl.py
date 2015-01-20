#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# Simple calculator; written for Python 3 (3.4.2).
# Thomas Backman (serenity@exscape.org), 2015-01-14 - 2015-01-19

# Features:
# * Readline support for history and input editing
# * Uses integer math where possible (for exact results)
# * Support for input of hexadecimal/octal/binary numbers (not output, though)
# * Integer sizes limited by amount of RAM only (floats are *not* arbitrary precision)
# * Proper order of operations
# * Built-in constants: e, pi
# * Supports variables
# * Chained comparisons: a > b > c works as in mathematics; things like a > b >= c == d also works
#   These are treated as (a > b) && (b > c), and (a > b) && (b > c) && (c == d), respectively.
# * On the other hand, c == (a > b) means to test a > b first; c is then tested against that 0 or 1
# * .help command
# * .vars command shows the value of all variables (except unchanged built-ins)
# * Supports built-in functions (sqrt, sin, cos, tan and so on, see .help for a complete list)
# * Value of last evaluation is accessible as _
# * # begins a comment (until end-of-line)

# TODO: update comment block above when statements are in
# TODO: elseif
# TODO: remember to add the above to the .help listing

# TODO: types
# TODO: tests for if/else, functions, strings and so on!

# TODO: inline if-statements (and unless) -- ternary can NOT use if/else syntax,
#       or "return x if y" becomes a bit ugly, as it could be "return x" if y, or
#       return "x if y else z". Might be easy to parse, but it doesn't look great either way.

from excalc.interpreter import evaluate, evaluate_expr
from excalc.version import __version__, __date__, __prompt__

import sys
import readline
import re

def print_error_pos(e):
    m = re.search('input position (\d+):(\d+)$', str(e))
    if m:
        (line, pos) = (int(m.group(1)), int(m.group(2)))
        assert line == 1
        print(" " * (pos - 1 + len(__prompt__)) + "^")

while True:
    try:
        input_str = input(__prompt__)
        try:
            results = evaluate_expr(input_str)
            if results is not None and len([r for r in results if r is not None]) > 0:
                print("\n".join([str(r) for r in results if r is not None]))
        except NameError as e:
            print("Name error: {}".format(str(e)))
        except OverflowError:
            print("Overflow: result is out of range")
        except SyntaxError as e:
            print_error_pos(e)
            print("Syntax error: {}".format(str(e)))
        except TypeError as e:
            print("Type error: {}".format(str(e)))
        except RuntimeError as e:
            print("BUG: {}".format(str(e)))
            sys.exit(1)

    except (KeyboardInterrupt, EOFError):
        print("")
        sys.exit(0)
