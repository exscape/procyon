#!/usr/bin/env python3

from .version import __prompt__

tokens = ('INT', 'OCT', 'BIN', 'HEX', 'FLOAT',           # Number literals
		  'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EXPONENT', # Math operators
		  'NOT',
		  'ANDAND', 'OROR',
		  'EQEQ', 'NOTEQ', 'LT', 'GT', 'LE', 'GE',       # Comparison operators
		  'LPAREN', 'RPAREN', 'ASSIGN', 'COMMA', 'SEMICOLON',
		  'IDENT', 'COMMAND')

# Matches e.g. 1., 1.4, 2.3e2 (230), 4e-3 (0.004)
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

# Tokens that don't need any transformations
t_IDENT = r'[A-Za-z_][A-Za-z0-9_]*'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_EXPONENT = r'\^'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NOT = r'!'
t_NOTEQ = r'!='
t_EQEQ = r'=='
t_ANDAND = r'&&'
t_OROR = r'\|\|'
t_GE = r'>='
t_LE = r'<='
t_LT = r'<'
t_GT = r'>'
t_ASSIGN = r'='
t_COMMA = r','
t_COMMAND = r'^\.[a-zA-Z]+\s*$'
t_SEMICOLON = r';'
# NOTE: don't add token rules for IF, ELSE etc.; see ply docs section 4.3

# Comments begin with # and last one line; whitespace outside of strings etc. is ignored
t_ignore_COMMENT = r'\#.*'
t_ignore = "\t\r\n "

def t_error(t):
	print (" " * (t.lexpos + len(__prompt__)) + "^")
	raise SyntaxError('Unexpected {} at input position {}'.format(t.value[0], t.lexpos))
