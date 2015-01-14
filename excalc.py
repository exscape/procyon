#!/usr/bin/env python3

import sys
from ply import lex, yacc
















def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""
	return 0






if __name__ == '__main__':
	input_str = "1 + ((5 - 3)^2)^3"
	expected = 65

	if len(sys.argv) == 2:
		input_str = sys.argv[1]
		expected = None

	result = evaluate(input_str)

	if expected is not None:
		if expected == result:
			print ("Success!")
		else:
			print ("Failed! Expected {}, got {}".format(expected, result))
	else:
		print ("Result: {}".format(result))
