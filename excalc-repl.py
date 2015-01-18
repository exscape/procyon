#!/usr/bin/env python3

# Simple calculator; written for Python 3 (3.4.2).
# Thomas Backman (serenity@exscape.org), 2015-01-14 - 2015-01-16

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

# TODO: refactor to better Python style
# TODO: support custom functions?
# TODO: if/else, return (?) -- allowing e.g. recursive factorial to be defined
# TODO: remember to add the above to the .help listing

from excalc.interpreter import evaluate
from excalc.version import __version__, __date__, __prompt__

import sys
import readline

while True:
	try:
		input_str = input(__prompt__)
		try:
			results = evaluate(input_str)
			if results is not None and len([r for r in results if r is not None]) > 0:
				print ("\n".join([str(r) for r in results if r is not None]))
		except KeyError as e:
			print ("Error: {}".format(str(e)[1:-1]))
		except OverflowError:
			print ("Overflow: result is out of range")
		except SyntaxError as e:
			print("Syntax error: {}".format(str(e)))
		except RuntimeError as e:
			print("BUG: {}".format(str(e)))
			sys.exit(1)

	except (KeyboardInterrupt, EOFError):
		print("")
		sys.exit(0)
