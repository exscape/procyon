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
# * .help command
# * .vars command shows the value of all variables (except unchanged built-ins)
# * Supports built-in functions (sqrt, sin, cos, tan and so on, see .help for a complete list)
# * Value of last evaluation is accessible as _
# * # begins a comment (until end-of-line)

# TODO: comment the parsing stuff before everything is forgotten :-)
# TODO: &&, || or perhaps "and", "or"; also not
# TODO: support custom functions?
# TODO: if/else, return (?) -- allowing e.g. recursive factorial to be defined
# TODO: remember to add the above to the .help listing
# TODO: unit testing, including testing exceptions for syntax errors etc

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

	except (KeyboardInterrupt, EOFError):
		print("")
		sys.exit(0)
