#!/usr/bin/env python3

import sys
from ply import lex, yacc

# TODO: unary minus
# TODO: comments, single and multi-line
# TODO: variables/assignment
# TODO: pre-defined functions (sqrt, sin, cos, tan, exp and a few other common ones)
# TODO: pre-defined *variables* (e, pi)
# TODO: error handling (lexing errors, syntax errors)

# Stuff used by the lexer

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

# Stuff used by the parser

precedence = (
	  ("left", "PLUS", "MINUS"),
	  ("left", "TIMES", "DIVIDE"),
	  ("left", "EXPONENT")
	  )

def p_error(p):
	print ('p_error:', p)


#
# Here's the grammar used:
# exp -> exp (PLUS|MINUS|TIMES|DIVIDE|EXPONENT) exp
# exp -> ( exp )
# exp -> number
# number -> INT | FLOAT
#

def p_exp_binop(p):
	'''exp : exp PLUS exp
	       | exp MINUS exp
	       | exp TIMES exp
	       | exp DIVIDE exp
	       | exp EXPONENT exp'''

	p[0] = ("binop", p[1], p[2], p[3])

def p_exp_paren(p):
	'exp : LPAREN exp RPAREN'
	p[0] = p[2]

def p_exp_int(p):
	'exp : INT'
	p[0] = ("int", p[1])

def p_exp_float(p):
	'exp : FLOAT'
	p[0] = ("float", p[1])













def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	print ('Lexing...')
	lexer = lex.lex()
	lexer.input(expr)
	while True:
		tok = lexer.token()
		if not tok: break
		print (tok)

	parser = yacc.yacc()

	parse_tree = parser.parse(expr, lexer=lexer)

	return evaluate_tree(parse_tree)

def evaluate_tree(tree):
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
