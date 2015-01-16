#!/usr/bin/env python3

import sys, readline
from ply import lex, yacc
import math

# Simple calculator; written for Python 3 (3.4.2).
# Thomas Backman (serenity@exscape.org), 2015-01-14 - 2015-01-16
__VERSION = '0.1a'
__DATE = '2015-01-16'
__debugparse = 0

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
# TODO: split source into multiple files (lexer/parser/interpreter)
# TODO: remember to add the above to the .help listing
# TODO: unit testing, including testing exceptions for syntax errors etc

__prompt = '> '

# Stuff used by the lexer

tokens = ('INT', 'OCT', 'BIN', 'HEX', 'FLOAT',
		  'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
		  'EXPONENT',
		  'LPAREN', 'RPAREN',
		  'ASSIGN', 'EQEQ', 'NOTEQ',
		  'LT', 'GT', 'LE', 'GE',
		  'COMMA', 'SEMICOLON',
		  'IDENT', 'COMMAND')

def t_FLOAT(t):
	r'\d+ (?:\.\d*)? e [+-]? \d+ | \d+\.\d*'
	t.value = float(t.value)
	return t

def t_BIN(t):
	r'0b[01]+'
	t.value = int(t.value, 2)
	return t

def t_OCT(t):
	r'0o[0-7]+'
	t.value = int(t.value, 8)
	return t

def t_HEX(t):
	r'0x[0-9A-Fa-f]+'
	t.value = int(t.value, 16)
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
t_NOTEQ = r'!='
t_EQEQ = r'=='
t_GE = r'>='
t_LE = r'<='
t_LT = r'<'
t_GT = r'>'
t_ASSIGN = r'='
t_COMMA = r','
t_COMMAND = r'^\.[a-zA-Z]+\s*$'
t_SEMICOLON = r';'
# NOTE: don't add token rules for IF, ELSE etc.; see ply docs section 4.3

t_ignore_HASH = r'\#.*'
t_ignore = "\t\r\n "

def t_error(t):
	print (" " * (t.lexpos + len(__prompt)) + "^")
	raise SyntaxError('Unexpected {} at input position {}'.format(t.value[0], t.lexpos))

# Stuff used by the parser

precedence = (
	  ("nonassoc", "SEMICOLON"),
	  ("right", "ASSIGN"),
	  ("left", "EQEQ", "NOTEQ", "LT", "GT", "LE", "GE"),
	  ("left", "PLUS", "MINUS"),
	  ("left", "TIMES", "DIVIDE"),
	  ("right", "UMINUS"),
	  ("right", "EXPONENT"),
	  )

def p_error(p):
	if p is None:
		raise SyntaxError('Unexpected end of input; unbalanced parenthesis or missing argument(s)?')
	else:
		print (" " * (p.lexpos + len(__prompt)) + "^")
		raise SyntaxError('Unexpected {} at input position {}'.format(p.type, p.lexpos))

def p_exps_one(p):
	'exps : exp'
	p[0] = [p[1]]

def p_exps_comps(p):
	'exps : comps'
	p[0] = [p[1]]

def p_exps_many(p):
	''' exps : exp SEMICOLON exps
		     | comps SEMICOLON exps'''
	p[0] = [p[1]] + p[3]

def p_exps_empty(p):
	'exps : '
	p[0] = []

def p_exp_binop(p):
	'''exp : exp PLUS exp
	       | exp MINUS exp
	       | exp TIMES exp
	       | exp DIVIDE exp
	       | exp EXPONENT exp'''

	p[0] = ("binop", p[1], p[2], p[3])

# These two rules following are very simple in terms of the function body,
# but the grammar rules were difficult to get right, in terms of comp/comps, not getting
# a tree with unnecessary nested comps (should be harmless, but ugly) and so on.
# All of the following need to work:
# 5 > 4: True
# 5 > 4 > 3: True
# (5 > 4) > 3: False, since (5 > 4) == 1, so 1 > 3 gives False
# (5 > 4 > 3) == 1: True
# ... and so on.
# Also see the comments for p_comps_many, for the rules for parsing a>b>c style expressions.
def p_comps_paren(p):
	'comps : LPAREN comps RPAREN'''
	p[0] = p[2]

# E.g. (a>b>c) == d, which generates the parse tree:
# ('comp', ('comps', [('comp', ('ident', 'a'), '>', ('ident', 'b')), ('comp', ('ident', 'b'), '>', ('ident', 'c'))]), '==', ('ident', 'd'))
# Or: A comparison of (a set of comparisons, a>b && b>c) == (d)
def p_comps_paren_comparison(p):
	'comps : LPAREN comps RPAREN compop exp'
	p[0] = ("comp", p[2], p[4], p[5])

def p_comps_one(p):
	'comps : comp'
	p[0] = ("comps", [p[1]])

# Support multiple comparisons:
# a > b
# ('comps', [('comp', ('ident', 'a'), '>', ('ident', 'b'))])
# a > b > c
# ('comps', [('comp', ('ident', 'a'), '>', ('ident', 'b')), ('comp', ('ident', 'b'), '>', ('ident', 'c'))])
# True if all comparisons in the list are true
def p_comps_many(p):
	'comps : comps compop exp'

	# Eww... So here's an example of how this line works.
	# While parsing a > b > c, the various parts refer to these values:       v p[2]
	# p =  [None, ('comps', [('comp', ('ident', 'a'), '>', ('ident', 'b'))]), '>',   ('ident', 'c')]
	#       ^p[0]  ^p[1][0] ^p[1][1] (the entire list)               ^p[1][1][-1][3] ^ p[3]
	p[0] = ("comps", p[1][1] + [("comp", p[1][1][-1][3], p[2], p[3])])

def p_comp_one(p):
	'''comp : exp compop exp'''
	args = []
	for i in range(1, len(p)):
		args.append(p[i])
#print("comp_one: args = ", args)
	p[0] = ("comp", p[1], p[2], p[3])

def p_compop(p):
	'''compop : EQEQ
	          | NOTEQ
	          | LT
	          | GT
	          | LE
	          | GE'''
	p[0] = p[1]

def p_exp_paren(p):
	'exp : LPAREN exp RPAREN'
	p[0] = p[2]

def p_exp_num(p):
	'''exp : INT
	       | HEX
	       | OCT
	       | BIN'''
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
__functions = {'sin': 1, 'cos': 1, 'tan': 1,
	           'exp': 1, 'log': 1, 'log10': 1, 'log2': 1,
			   'asin': 1, 'acos': 1, 'atan': 1, 'atan2': 2,
			   'sinh': 1, 'cosh': 1, 'tanh': 1,
			   'asinh': 1, 'acosh': 1, 'atanh': 1,
			   'abs': 1, 'sqrt': 1, 'ceil': 1, 'floor': 1, 'trunc': 1, 'round': 2}

# Built-in constants; there are overwritable by design
__initial_state = {'e': math.e, 'pi': math.pi}
__state = __initial_state.copy()

def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	if len(expr.rstrip()) == 0:
		return None

	lexer = lex.lex(debug=False,optimize=False)
	parser = yacc.yacc(debug=False, start="exps",optimize=False)
	parse_tree = parser.parse(expr, lexer=lexer, debug=__debugparse)

	return evaluate_all(parse_tree)

def evaluate_all(trees):
	""" Evaluates a full set of expressions e.g. 1+2; 3+4: 5+6 and returns a list of results """

	results = []
	for tree in trees:
		if len(tree) == 0: continue
		result = evaluate_tree(tree)
		results.append(result)
		if result is not None:
			__state['_'] = result

	return results

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

	elif kind == "comps":
		args = tree[1]
		return all([evaluate_tree(tree) for tree in args])

	elif kind == "comp":
		(left_child, op, right_child) = tree[1:]
		left = evaluate_tree(left_child)
		right = evaluate_tree(right_child)

		if op == '==':
			return left == right
		elif op == '!=':
			return left != right
		elif op == '>':
			return left > right
		elif op == '<':
			return left < right
		elif op == '<=':
			return left <= right
		elif op == '>=':
			return left >= right

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

		func = None
		try:
			func = getattr(math, func_name)
		except AttributeError:
			func = getattr(sys.modules['builtins'], func_name)

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
		elif cmd_name == 'help':
			print("# exCalc v" + __VERSION + ", " + __DATE)
			print("# Supported operators: + - * / ^ ( ) = == != < > >= <=")
			print("# Comments begin with a hash sign, as these lines do.")
			print("# = assigns, == tests equality (!= tests non-equality), e.g.:")
			print("# a = 5")
			print("# a == 5 # returns True")
			print("#")
			print("# Supported commands:")
			print("# .help - this text")
			print("# .vars - show all variables, except non-modified builtins")
			print("#")
			print("# Supported functions (number of arguments, if not 1):")
			print("# " + ", ".join(sorted(["{}{}".format(f, "({})".format(__functions[f]) if __functions[f] > 1 else "") for f in __functions])))
			print("#")
			print("# Built-in constants (names are re-assignable):")
			print("# " + ", ".join(sorted(__initial_state)))
			print("# Use _ to access the last result, e.g. 12 + 2 ; _ + 1 == 15 # returns True")
			print("# Use 0x1af, 0o175, 0b11001 etc. to specify hexadecimal/octal/binary numbers.")
		else:
			raise SyntaxError("Unknown command {}".format(cmd_name))

		return None

	print("BUG: reached end of evaluate_tree for kind={}, tree: {}".format(kind,tree))
	sys.exit(1)

if __name__ == '__main__':
	while True:
		try:
			input_str = input(__prompt)
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
