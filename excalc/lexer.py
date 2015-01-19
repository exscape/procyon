#!/usr/bin/env python3

from .version import __prompt__

keywords = ('if', 'else', 'func', 'return')

tokens = ['INT', 'OCT', 'BIN', 'HEX', 'FLOAT',           # Number literals
		  'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EXPONENT', # Math operators
		  'NOT',
		  'ANDAND', 'OROR',
		  'EQEQ', 'NOTEQ', 'LT', 'GT', 'LE', 'GE',       # Comparison operators
		  'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMICOLON', 'COMMA',
		  'ASSIGN',
		  'IDENT', 'COMMAND', 'STRING'] + [k.upper() for k in keywords]

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

def t_IDENT(t):
	r'[A-Za-z_][A-Za-z0-9_]*'
	if t.value in keywords:
		t.type = t.value.upper()
	return t

# Match a double quote, followed by any number of:
# 1) Anything except backslashes and quotes, or
# 2) a backslash followed by anything,
# finally followed by a lone quote.
# This matches all strings including ones with
# escaped double quotes inside.
def t_STRING(t):
	r'"(?:[^"\\]|\\.)*"'
	t.value = t.value[1:-1] # Strip quotes
	return t

# Tokens that don't need any transformations
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
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_ASSIGN = r'='
t_COMMA = r','
t_COMMAND = r'^\.[a-zA-Z]+\s*$'
t_SEMICOLON = r';'
# NOTE: don't add token rules for IF, ELSE etc.; see ply docs section 4.3

# Comments begin with # and last one line; whitespace outside of strings etc. is ignored
t_ignore_COMMENT = r'\#.*'
t_ignore = "\t\r\v "

def t_newline(t):
	r'\n+'
	t.lexer.lineno += len(t.value)

def column(token):
	last_cr = token.lexer.lexdata.rfind('\n', 0, token.lexpos)
	if last_cr < 0:
		return token.lexpos + 1
	else:
		return token.lexpos - last_cr

def t_error(t):
	raise SyntaxError('Unexpected {} at input position {}:{}'.format(t.value[0], t.lineno, column(t)))
