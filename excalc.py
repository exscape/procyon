#!/usr/bin/env python3

import sys, readline
from ply import lex, yacc
import math

# TODO: comments, single and multi-line...?
# TODO: pre-defined functions (sqrt, sin, cos, tan, exp and a few other common ones)
# TODO: error handling (lexing errors, syntax errors)

# Stuff used by the lexer

tokens = ('INT', 'FLOAT',
		  'PLUS', 'MINUS',
		  'TIMES', 'DIVIDE',
		  'EXPONENT',
		  'LPAREN', 'RPAREN',
		  'ASSIGN', 'EQEQ',
		  'IDENT')

def t_FLOAT(t):
	r'\d+ (?:\.\d*)? e [+-]? \d+ | \d+\.\d*'
	t.value = float(t.value)
	return t

def t_INT(t):
	r'\d+'
	t.value = int(t.value)
	return t

t_IDENT = r'[A-Za-z_][A-Za-z0-9_]*'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EXPONENT = r'\^'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_EQEQ = r'=='
t_ASSIGN = r'='

t_ignore = "\t\r\n "

def t_error(t):
	print ('t_error:', t)

# Stuff used by the parser

precedence = (
	  ("left", "ASSIGN"),
	  ("left", "EQEQ"),
	  ("left", "PLUS", "MINUS"),
	  ("left", "TIMES", "DIVIDE"),
	  ("right", "UMINUS"),
	  ("right", "EXPONENT"),
	  )

def p_error(p):
	print ('p_error:', p)

def p_exp_binop(p):
	'''exp : exp PLUS exp
	       | exp MINUS exp
	       | exp TIMES exp
	       | exp DIVIDE exp
	       | exp EXPONENT exp
	       | exp EQEQ exp'''

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

def p_exp_ident(p):
	'exp : ident'
	p[0] = p[1]

def p_exp_uminus(p):
	'exp : MINUS exp %prec UMINUS'
	# Matches -exp and uses precedence UMINUS instead of the usual MINUS
	p[0] = ("uminus", p[2])

def p_ident(p):
	'ident : IDENT'
	p[0] = ("ident", p[1])

def p_assign(p):
	'exp : ident ASSIGN exp'
	p[0] = ("assign", p[1], p[3])

# End of parser definitions

__state = {'e': math.e, 'pi': math.pi}

def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	lexer = lex.lex(debug=False)
	parser = yacc.yacc(debug=False)
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
		elif op == '==':
			return left == right

	elif kind == "int":
		return tree[1]
	elif kind == "float":
		return tree[1]
	elif kind == "uminus":
		return -evaluate_tree(tree[1])
	elif kind == "ident":
		name = tree[1]
		try:
			return __state[name]
		except KeyError:
			raise KeyError('unknown variable name "{}"'.format(name))
	elif kind == "assign":
		name = tree[1][1]
		val = tree[2]
		__state[name] = evaluate_tree(val)

		return __state[name]

	print("ERROR: reached end of evaluate_tree for tree", tree)
	sys.exit(1)

if __name__ == '__main__':
	while True:
		try:
			input_str = input('>>> ')
			try:
				result = evaluate(input_str)
				print (result)
			except KeyError as e:
				print ("Error: {}".format(str(e)[1:-1]))
			except OverflowError:
				print ("Overflow: result is out of range")
		except (KeyboardInterrupt, EOFError):
			print("")
			sys.exit(0)
