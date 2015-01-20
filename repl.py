#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See README.md for information and such.

### HIGH PRIORITY TODO ITEMS:
# TODO: start using custom exception classes, as interpreter bugs are caught by accident now
# TODO: elseif

### Lower priority:
# TODO: function definitions can shadow built-ins; is that desirable or a bug?
# TODO: REPL: multi-line statements; "import"-ish functionality for loading code
# TODO: resolve shift-reduce conflicts for the comparison operators (PLY parses it as intended,
#       but it does warn)
# TODO: loops! for, while? do while?
# TODO: lists! Or "arrays"? Perhaps after static typing?
# TODO: types?
# TODO: inline if-statements (and unless) -- ternary can NOT use if/else syntax,
#       or "return x if y" becomes a bit ugly, as it could be "return x" if y, or
#       return "x if y else z". Might be easy to parse, but it doesn't look great either way.

# TODO: support reading programs from files (via sys.argv to intr.py)
# TODO: test ^ error pointing with comments
# TODO: fix ^ pointing with tab indentation

from procyon import evaluate, evaluate_command
from procyon.common import VERSION, DATE, PROMPT

import sys
import readline
import re

def print_error_pos(e):
    m = re.search('input position (\d+):(\d+)$', str(e))
    if m:
        (line, pos) = (int(m.group(1)), int(m.group(2)))
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
