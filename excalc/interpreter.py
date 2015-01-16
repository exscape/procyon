#!/usr/bin/env python3

import math
import sys
from .version import __version__, __date__, __debugparse__
from ply import lex, yacc
import excalc.lexer as lexer
import excalc.parser as parser

# Built-in functions and number of arguments
__functions = {'sin': 1, 'cos': 1, 'tan': 1,
	           'exp': 1, 'log': 1, 'log10': 1, 'log2': 1,
			   'asin': 1, 'acos': 1, 'atan': 1, 'atan2': 2,
			   'sinh': 1, 'cosh': 1, 'tanh': 1,
			   'asinh': 1, 'acosh': 1, 'atanh': 1,
			   'abs': 1, 'sqrt': 1, 'ceil': 1, 'floor': 1,
			   'trunc': 1, 'round': 2}

# Built-in constants; there are overwritable by design
__initial_state = {'e': math.e, 'pi': math.pi}
__state = __initial_state.copy()

def evaluate(expr):
	""" Evaluates an expression (as a string) and lexes/parses it, then returns the result"""

	if len(expr.rstrip()) == 0:
		return None

	lex_lexer = lex.lex(module=lexer, debug=False, optimize=True)
	yacc_parser = yacc.yacc(module=parser, debug=False, start="exps")
	parse_tree = yacc_parser.parse(expr, lexer=lex_lexer, debug=__debugparse__)

	return __evaluate_all(parse_tree)

def __evaluate_all(trees):
	""" Evaluates a full set of expressions e.g. 1+2; 3+4: 5+6 and returns a list of results """

	results = []
	for tree in trees:
		if len(tree) == 0: continue
		result = __evaluate_tree(tree)
		results.append(result)
		if result is not None:
			__state['_'] = result

	return results

def __evaluate_tree(tree):
	""" Recursively evalutates a parse tree and returns the result. """

	kind = tree[0]

	if kind == "binop":
		(left_child, op, right_child) = tree[1:]
		left = __evaluate_tree(left_child)
		right = __evaluate_tree(right_child)

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
		return all([__evaluate_tree(tree) for tree in args])

	elif kind == "comp":
		(left_child, op, right_child) = tree[1:]
		left = __evaluate_tree(left_child)
		right = __evaluate_tree(right_child)

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
		return -__evaluate_tree(tree[1])
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
		__state[name] = __evaluate_tree(val)
		return __state[name]
	elif kind == "func":
		func_name = tree[1][1]
		args = tree[2]

		if not func_name in __functions:
			raise SyntaxError('unknown function "{}"'.format(func_name))

		if len(args) != __functions[func_name]:
			raise SyntaxError('{} requires exactly {} arguments, {} provided'.format(func_name, __functions[func_name], len(args)))

		args = [__evaluate_tree(arg) for arg in args]

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
			print("# exCalc v" + __version__ + ", " + __date__)
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

	print("BUG: reached end of __evaluate_tree for kind={}, tree: {}".format(kind,tree))
	sys.exit(1)