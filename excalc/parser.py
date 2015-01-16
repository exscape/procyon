#!/usr/bin/env python3

from .version import __prompt__
from .lexer import tokens

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
		print (" " * (p.lexpos + len(__prompt__)) + "^")
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
