#!/usr/bin/env python3

import sys
from ply import lex, yacc

# TODO: comments, single and multi-line
# TODO: variables/assignment
# TODO: pre-defined functions (sin, cos, tan, exp and a few other common ones)
# TODO: pre-defined *variables* (e, pi)

tokens = ('INT', 'FLOAT',
		  'PLUS', 'MINUS',
		  'TIMES', 'DIVIDE',
		  'EXPONENT',
		  'LPAREN', 'RPAREN')

def t_FLOAT(t):
	r'\d\.\d*'
	t.value = float(t.value)
	return t

def t_INT(t):
	r'\d+'
	t.value = int(t.value)
	return t

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EXPONENT = r'\^'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore = "\t\r\n "

def t_error(t):
	print ('t_error:', t)
















def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	print ('Lexing...')
	lexer = lex.lex()
	lexer.input(expr)
	while True:
		tok = lexer.token()
		if not tok: break
		print (tok)

	return 0

if __name__ == '__main__':
	input_str = "1 + ((5 - 3.2)^2)^(3-1+1)"
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
