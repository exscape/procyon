#!/usr/bin/env python3

from .version import __prompt__
from .lexer import tokens

# Operator associativity and precedence rules
# From lowest to highest precedence
precedence = (
	  ("nonassoc", "SEMICOLON"),
	  ("right", "ASSIGN"),
	  ("left", "EQEQ", "NOTEQ", "LT", "GT", "LE", "GE"),
	  ("left", "PLUS", "MINUS"),
	  ("left", "TIMES", "DIVIDE"),
	  ("right", "UMINUS", "NOT"),
	  ("right", "EXPONENT"),
)

# Throw exceptions on parse errors
def p_error(p):
	if p is None:
		raise SyntaxError('Unexpected end of input; unbalanced parenthesis or missing argument(s)?')
	else:
		print (" " * (p.lexpos + len(__prompt__)) + "^")
		raise SyntaxError('Unexpected {} at input position {}'.format(p.type, p.lexpos))

###
### TOP LEVEL ELEMENTS
###

# A set of expressions such as "1+2 ; sqrt(2)" is allowed at the top level
def p_toplevel_expset(p):
	'toplevel : expset'
	p[0] = p[1]

# Commands (e.g. ".help") are also allowed at the top level
def p_toplevel_command(p):
	'toplevel : command'
	p[0] = [p[1]]

# A set of expressions can be a singleton list of [expression], or...
def p_expset_one(p):
	'expset : exp'
	p[0] = [p[1]]

# ... such a list, concatenated with a list of more expressions
def p_expset_many(p):
	' expset : exp SEMICOLON expset'
	p[0] = [p[1]] + p[3]

# Expression sets may be empty
def p_expset_empty(p):
	'expset : '
	p[0] = []

###
### MATH OPERATIONS
###

# All math operations with two operands
def p_exp_binop(p):
	'''exp : exp PLUS exp
	       | exp MINUS exp
	       | exp TIMES exp
	       | exp DIVIDE exp
	       | exp EXPONENT exp'''

	p[0] = ("binop", p[1], p[2], p[3])

# !
def p_exp_not(p):
	'exp : NOT exp'
	p[0] = ("not", p[2])

# Unary minus is a special case, since it uses the same operand
# as a - b, yet this minus sign has much higher precedence, and is
# also right-associative
def p_exp_uminus(p):
	'exp : MINUS exp %prec UMINUS'
	# Matches -exp and uses precedence UMINUS instead of the usual MINUS
	p[0] = ("uminus", p[2])

###
### COMPARISONS
###

### All of the following need to work:
### 5 > 4: True
### 5 > 4 > 3: True
### (5 > 4) > 3: False, since (5 > 4) evaluates to 1, so 1 > 3 gives False
### (5 > 4 > 3 == 1): False (3 != 1)
### 1 == (5 > 4 > 3): True
### ... and so on.

# a > b             -> ('comp', [('ident', 'a'), '>', ('ident', 'b')])
# a > b >= c        -> ('comp', [('ident', 'a'), '>', ('ident', 'b'), '>=', ('ident', 'c')])
# (a > b >= c) == d -> ('comp', [('comp', [('ident', 'a'), '>', ('ident', 'b'), '>=', ('ident', 'c')]), '==', ('ident', 'd')])

# Group all comparison operators as an element, to simplify comparisons below
def p_compop(p):
	'''compop : EQEQ
	          | NOTEQ
	          | LT
	          | GT
	          | LE
	          | GE'''
	p[0] = p[1]

# Handle comparisons; both a > b and a > b > c ... style expressions are handled here
def p_comp(p):
	'comp : exp compop exp'

	if p[3][0] != 'comp':
		# Single comparison (or just the first in a chain)
		p[0] = ('comp', [p[1], p[2], p[3]])
	else:
		# Chained comparison: a bit trickier
		p[0] = ('comp', [p[1]] + [p[2]] + p[3][1] )

# Comparisons such as c == (a > b) fail without this rule.
# The other case, e.g. (a > b) == c, is handled correctly by p_comp above.
def p_comp_paren(p):
	'comp : exp compop LPAREN comp RPAREN'
	p[0] = ('comp', [p[1], p[2], p[4]])

###
### EXPRESSIONS
###

# Comparisons are expressions
def p_exp_comp(p):
	'exp : comp'
	p[0] = p[1]

# (exp) is itself an expression. The parser handles the grouping and so on,
# so we only need to copy the expression here.
def p_exp_paren(p):
	'exp : LPAREN exp RPAREN'
	p[0] = p[2]

# Handle all integer types
def p_exp_num(p):
	'''exp : INT
	       | HEX
	       | OCT
	       | BIN'''
	p[0] = ("int", p[1])

# Floats are stored differently than ints
def p_exp_float(p):
	'exp : FLOAT'
	p[0] = ("float", p[1])

# Identifiers can be expressions (e.g. variables); the interpreter later
# checks whether they make sense or not (since e.g. function names
# are also identifiers, and expressions like cos = 10 don't make sense).
def p_exp_ident(p):
	'exp : ident'
	p[0] = p[1]

# Function calls are expressions (their return values are, at least!)
def p_exp_func(p):
	'exp : ident LPAREN args RPAREN'
	p[0] = ("func", p[1], p[3])

# TODO: reduce ambiguity and test that everything still works
# Function arguments
def p_args_many(p):
	'args : args COMMA args'
	p[0] = p[1] + p[3]

# Function arguments
def p_args_one(p):
	'args : exp'
	p[0] = [p[1]]

###
### MISCELLANEOUS RULES
###

# Simple enough.
def p_ident(p):
	'ident : IDENT'
	p[0] = ("ident", p[1])

# e.g. some_var = (2+3)^2; this is an expression that returns exp
def p_assign(p):
	'exp : ident ASSIGN exp'
	p[0] = ("assign", p[1], p[3])

# All commands begin with a dot; we strip that away here
def p_command(p):
	'command : COMMAND'
	p[0] = ("command", p[1][1:])
