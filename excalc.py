#!/usr/bin/env python3

import sys, readline
from ply import lex, yacc
import math

# Simple calculator; written for Python 3 (3.4.2).
# Thomas Backman (serenity@exscape.org), 2015-01-14
#
# Features:
# * Readline support for history and input editing
# * Uses integer math where possible (for exact results)
# * Integer sizes limited by amount of RAM only (floats are *not* arbitrary precision)
# * Proper order of operations
# * Supports built-in functions (sqrt, sin, cos, tan, exp, log/log10/log2)
# * Built-in constants: e, pi
# * Supports variables
# * Value of last evaluation is accessible as _
# * # begins a comment (until end-of-line)
# * .vars command shows the value of all variables (except unchanged built-ins)

# TODO: support custom functions?

# Stuff used by the lexer

tokens = ('INT', 'FLOAT',
		  'PLUS', 'MINUS',
		  'TIMES', 'DIVIDE',
		  'EXPONENT',
		  'LPAREN', 'RPAREN',
		  'ASSIGN', 'EQEQ',
		  'IDENT',
		  'COMMA', 'HASH',
		  'COMMAND')

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
t_COMMA = r','
t_COMMAND = r'^.[a-zA-Z]+\s*$'

def t_HASH(t):
	r'\#.*'
	# Comment: ignore the rest of the line
	pass

t_ignore = "\t\r\n "

def t_error(t):
	raise SyntaxError('Unexpected {} at input position {}'.format(t.value[0], t.lexpos))

# Stuff used by the parser

precedence = (
	  ("right", "ASSIGN"),
	  ("left", "EQEQ"),
	  ("left", "PLUS", "MINUS"),
	  ("left", "TIMES", "DIVIDE"),
	  ("right", "UMINUS"),
	  ("right", "EXPONENT"),
	  )

def p_error(p):
	if p is None:
		raise SyntaxError('Unexpected end of input; unbalanced parenthesis or missing argument(s)?')
	else:
		raise SyntaxError('Unexpected {} at input position {}'.format(p.type, p.lexpos))

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

def p_exp_func(p):
	'exp : ident LPAREN args RPAREN'
	p[0] = ("func", p[1], p[3])

def p_args_many(p):
	'args : args COMMA args'
	p[0] = p[1] + p[3]

def p_args_one(p):
	'args : exp'
	p[0] = [p[1]]

def p_ident(p):
	'ident : IDENT'
	p[0] = ("ident", p[1])

def p_assign(p):
	'exp : ident ASSIGN exp'
	p[0] = ("assign", p[1], p[3])

# Ugly, but it works (shouldn't really be an expression)
def p_exp_command(p):
	'exp : command'
	p[0] = p[1]

def p_command(p):
	'command : COMMAND'
	p[0] = ("command", p[1][1:])

# End of parser definitions

# Built-in functions and number of arguments
__functions = {'sin': 1, 'cos': 1, 'tan': 1, 'exp': 1, 'sqrt': 1, 'log': 1, 'log10': 1, 'log2': 1, 'atan2': 2}

# Built-in constants; there are overwritable by design
__initial_state = {'e': math.e, 'pi': math.pi}
__state = __initial_state.copy()

def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	lexer = lex.lex(debug=False)
	parser = yacc.yacc(debug=False)
	parse_tree = parser.parse(expr, lexer=lexer)

	result = evaluate_tree(parse_tree)
	__state['_'] = result
	return result

def evaluate_tree(tree):
	""" Recursively evalutates a parse tree and returns the result. """
	kind = tree[0]

	if kind == "binop":
		(left_child, op, right_child) = tree[1:]

		left = evaluate_tree(left_child)
		right = evaluate_tree(right_child)

		if op == '+':
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

	elif kind in ("int", "float"):
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

		if name in __functions:
			raise KeyError('cannot assign to built-in function "{}"'.format(name))

		val = tree[2]
		__state[name] = evaluate_tree(val)
		return __state[name]
	elif kind == "func":
		func_name = tree[1][1]
		args = tree[2]

		if not func_name in __functions:
			raise SyntaxError('unknown function "{}"'.format(func_name))

		if len(args) != __functions[func_name]:
			raise SyntaxError('{} requires exactly {} arguments, {} provided'.format(func_name, __functions[func_name], len(args)))

		args = [evaluate_tree(arg) for arg in args]

		func = getattr(math, func_name)
		return func(*args)
	elif kind == "command":
		cmd_name = tree[1]
		if cmd_name == 'vars':
			# Bit of a mess... Fetch each variable name.
			# Ignore _, and ignore pre-defined constants (e.g. e, pi)
			# *UNLESS* the user has assigned other values to those names.
			vars = [v for v in __state if (v != '_' and not (v in __initial_state and __initial_state[v] == __state[v]))]

			for var in sorted(vars):
				print("{}:\t{}".format(var, __state[var]))
		else:
			raise SyntaxError("Unknown command {}".format(cmd_name))

		return None

	print("BUG: reached end of evaluate_tree for tree:", tree)
	sys.exit(1)

if __name__ == '__main__':
	while True:
		try:
			input_str = input('>>> ')
			try:
				result = evaluate(input_str)
				if result is not None:
					# Commands return None
					print (result)
			except KeyError as e:
				print ("Error: {}".format(str(e)[1:-1]))
			except OverflowError:
				print ("Overflow: result is out of range")
			except SyntaxError as e:
				print("Syntax error: {}".format(str(e)))

		except (KeyboardInterrupt, EOFError):
			print("")
			sys.exit(0)
