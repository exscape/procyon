#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

from .common import ProcyonSyntaxError

#
# Proycon lexer definitions.
# If you know how a lexer works, nothing in this file should be very
# surprising.
# The actual lexing is done by ply.lex; the call to that is located in
# interpreter.py, in evaluate().
#
# Token rules that use functions are evaluated in the order they are defined,
# while string rules are sorted by length and evaluated longest first.
#

keywords = ('if', 'else', 'while', 'break', 'continue', 'func', 'return')

tokens = ['INT', 'OCT', 'BIN', 'HEX', 'FLOAT',             # Number literals
          'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EXPONENT', 'REMAINDER', 'INTDIVIDE',
          'NOT',
          'ANDAND', 'OROR',                                # Logical operators
          'EQEQ', 'NOTEQ', 'LT', 'GT', 'LE', 'GE',         # Comparison operators
          'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMICOLON', 'COMMA',
          'ASSIGN', 'ASSIGN_PLUS', 'ASSIGN_MINUS', 'ASSIGN_TIMES', 'ASSIGN_DIVIDE',
          'ASSIGN_EXPONENT', 'ASSIGN_REMAINDER', 'ASSIGN_INTDIVIDE',
          'IDENT', 'STRING', 'ELSEIF'] + [k.upper() for k in keywords]

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

# This MUST be located above IDENT, or it will be lexed as two separate
# IDENTs, "else" and "if"! This must be a single token, to simplify the parser's work.
# Combined with requiring braces around if/else blocks, this should eliminate
# all ambiguities (such as the "dangling else" problem).
def t_ELSEIF(t):
    r'else\ if'
    t.type = "ELSEIF"
    return t

def t_IDENT(t):
    r'\$?[A-Za-z_][A-Za-z0-9_]*'
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
    t.value = t.value[1:-1]
    return t

# Tokens that don't need any transformations
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_INTDIVIDE = r'//'
t_DIVIDE = r'/'
t_EXPONENT = r'\^'
t_REMAINDER = r'%'
t_ASSIGN_PLUS = r'\+='
t_ASSIGN_MINUS = r'-='
t_ASSIGN_TIMES = r'\*='
t_ASSIGN_INTDIVIDE = r'//='
t_ASSIGN_DIVIDE = r'/='
t_ASSIGN_EXPONENT = r'\^='
t_ASSIGN_REMAINDER = r'%='
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
t_SEMICOLON = r';'

# Comments begin with # and last one line; whitespace outside of strings etc. is ignored.
# Newlines are not ignored (see below), as we need them to track line numbers.
t_ignore_COMMENT = r'\#.*'
t_ignore = "\t\r\v "

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def column(token):
    """ Calculate the (1-indexed) column number for a given token. """
    last_cr = token.lexer.lexdata.rfind('\n', 0, token.lexpos)
    if last_cr < 0:
        return token.lexpos + 1
    else:
        return token.lexpos - last_cr

def t_error(t):
    raise ProcyonSyntaxError((t.lineno, column(t), 'unexpected {}'.format(
        t.value[0])))
