#!/usr/bin/env python3

import sys, readline
from ply import lex, yacc

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
	  ("right", "UMINUS"),
	  ("left", "EXPONENT"),
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

def p_exp_uminus(p):
	'exp : MINUS exp %prec UMINUS'
	# Matches (empty) -exp and uses precedence UMINUS instead of the usual MINUS
	p[0] = ("uminus", p[2])












def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	lexer = lex.lex(optimize=False)
	parser = yacc.yacc()
	parse_tree = parser.parse(expr, lexer=lexer)

	return evaluate_tree(parse_tree)

def evaluate_tree(tree):
	""" Recursively evalutates a parse tree and returns the result. """
	kind = tree[0]

	if kind == "binop":
		(left_child, op, right_child) = tree[1:]

		left = evaluate_tree(left_child)
		right = evaluate_tree(right_child)

		if   op == '+':
			return left + right
		elif op == '-':
			return left - right
		elif op == '*':
			return left * right
		elif op == '/':
			return left / right
		elif op == '^':
			return left ** right

	elif kind == "int":
		return tree[1]
	elif kind == "float":
		return tree[1]
	elif kind == "uminus":
		return -evaluate_tree(tree[1])

	print("ERROR: reached end of evaluate_tree for tree", tree)
	sys.exit(1)

if __name__ == '__main__':
	while True:
		input_str = input('>>> ')
		if input_str == "":
			sys.exit(0)
		result = evaluate(input_str)
		print (result)
