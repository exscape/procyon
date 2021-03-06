#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

from .lexer import tokens, column
from .common import ProcyonSyntaxError
from .ast import (Node, Value, Ident, BinaryOp, UnaryOp, Function, Conditional,
                  While, FunctionCall, ControlFlowStatement, Comparison, ComparisonOp)

#
# Procyon parser definitions.
# The actual parsing (ply.yacc) is called from interpreter.py, in evaluate().
#

# Operator associativity and precedence rules
# From lowest to highest precedence.
# These are similar to C, but not identical (a > b > c is more useful here than in C).
#
# CHAINCOMP is used to resolve/silence 6 practically identical shift-reduce conflicts,
# one per comparison operator.
# When the parser sees "a > b >= c", it first parses "a > b" and reduces that to
# a comp (comparison), but when it then sees another comparison operator following that,
# it doesn't know whether to further reduce that "a > b" to an exp (expression), or
# to shift the >= and reduce later, as there are rules for *both* exp >= exp and
# comp >= exp, and "a > b" is both a valid comp and a valid exp.
# We *always* want it to shift, as it does by default, but I felt that making this
# explicit, to silence the warnings, might be nice.
#
# The reason why adding CHAINCOMP helps is that it has a lower precedence than comparisons,
# and when PLY sees a lookahead operator with *higher* precedence than the current,
# it shifts.
# So this rule gives "a > b" a low precedence, so that the comparison with c has a higher one.
#
# This is easy to see with math, where * has higher precedence than +:
# 1 + 3 . * 4
# where the dot is where the parser is. * is the current lookahead, and it doesn't know about
# the 4 at all yet.
# If it reduces 1+3, the end result is (1+3)*4, which is incorrect.
# If it shifts, and then shifts the 4, it ends up with 1 + 3 * 4 on the stack,
# which it can reduce by first by reducing 3 * 4, and then by reducing 1 + (3 * 4).
precedence = (
    ("nonassoc", "SEMICOLON"),
    ("right", "ASSIGN", "ASSIGN_PLUS", "ASSIGN_MINUS", "ASSIGN_TIMES", "ASSIGN_DIVIDE",
        "ASSIGN_EXPONENT", "ASSIGN_REMAINDER", "ASSIGN_INTDIVIDE"),
    ("left", "OROR"),
    ("left", "ANDAND"),
    ("left", "CHAINCOMP"),  # See note above
    ("left", "EQEQ", "NOTEQ", "LT", "GT", "LE", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "INTDIVIDE", "REMAINDER"),
    ("right", "UMINUS", "NOT"),
    ("right", "EXPONENT"),
)

def pos(p, index):
    """ Find position for the AST. Returns a (line, col) tuple, given a parse tree and an index. """
    line = p.lineno(index)
    col = column(p.lexer.lexdata, p.lexpos(index))

    return (line, col)

# Raise exceptions on parse errors
def p_error(p):
    if p is None:
        raise ProcyonSyntaxError(
            (-1, -1), 'unexpected end of input; unbalanced parenthesis or missing argument(s)?')
    else:
        raise ProcyonSyntaxError(
            (p.lineno, column(p.lexer.lexdata, p.lexpos)),
            'unexpected {}({})'.format(p.type, p.value))

###
### TOP LEVEL ELEMENTS
###

# A list of statements is allowed at the top level
# (Note that since we have statement -> exp, this means that
#  a list of expressions is also allowed; or a mix of the two.)
def p_toplevel_statements(p):
    'toplevel : statements'
    p[0] = p[1]

##
### MATH OPERATIONS
##

# All math operations with two operands
def p_exp_binop(p):
    '''exp : exp PLUS exp
           | exp MINUS exp
           | exp TIMES exp
           | exp DIVIDE exp
           | exp INTDIVIDE exp
           | exp EXPONENT exp
           | exp REMAINDER exp'''

    p[0] = BinaryOp(pos(p, 2), "math", p[1], p[3], p[2])

# a += 5 style rules; these are right-associative expressions,
# such that "a = 2; b = 10; a += b -= 4" sets b = 6 and a = 8.
# (I would recommend against using such expressions, of course, but they should work.)
def p_exp_binop_assign(p):
    '''exp : ident ASSIGN_PLUS exp
           | ident ASSIGN_MINUS exp
           | ident ASSIGN_TIMES exp
           | ident ASSIGN_DIVIDE exp
           | ident ASSIGN_EXPONENT exp
           | ident ASSIGN_REMAINDER exp
           | ident ASSIGN_INTDIVIDE exp'''
    op = BinaryOp(pos(p, 2), "math", p[1], p[3], p[2][:-1])
    p[0] = BinaryOp(pos(p, 2), "assign", p[1], op, '=')

# !
def p_exp_not(p):
    'exp : NOT exp'
    p[0] = UnaryOp(pos(p, 1), '!', p[2])

# Unary minus is a special case, since it uses the same operand
# as a - b, yet this minus sign has much higher precedence, and is
# also right-associative
def p_exp_uminus(p):
    'exp : MINUS exp %prec UMINUS'
    # Matches -exp and uses precedence UMINUS instead of the usual MINUS
    p[0] = UnaryOp(pos(p, 1), '-', p[2])

##
### COMPARISONS
##

# All of the following need to work:
# 5 > 4: True
# 5 > 4 > 3: True
# (5 > 4) > 3: False, since (5 > 4) evaluates to 1, so 1 > 3 gives False
# (5 > 4 > 3 == 1): False (3 != 1)
# 1 == (5 > 4 > 3): True
# ... and so on.
#
# a > b             -> ('comp', [('ident', 'a'), '>', ('ident', 'b')])
# a > b >= c        -> ('comp', [('ident', 'a'), '>', ('ident', 'b'), '>=', ('ident', 'c')])
# (a > b >= c) == d -> ('comp', [(comp, ... from prev line), '==', ('ident', 'd')])

# Handle single comparisons such as a > b, a == b etc.
# a and b may be more complex expressions, though.
def p_comp_one(p):
    '''comp : exp EQEQ exp
            | exp NOTEQ exp
            | exp LT exp
            | exp LE exp
            | exp GT exp
            | exp GE exp'''

    op = ComparisonOp(pos(p, 2), p[2])
    p[0] = Comparison(pos(p, 2), [p[1], op, p[3]])

# Handle chained comparisons such as a > b > c, a < b <= c > d != e, and so on.
# The rule above is always executed first. For the example of a > b > c == d:
# comp_one: a > b is turned into (a > b)
# comp_chained: (a > b) > c is turned into a > b > c
# comp_chained: (a > b > c) == d is turned into a > b > c == d
#
# Note that if the input is (verbatim) "(a > b > c) == d" the behaviour is
# different, by design! In that case, "a > b > c" is evaluated first,
# to either 1 or 0. That boolean is then compared against d.
def p_comp_chained(p):
    '''comp : comp EQEQ exp
            | comp NOTEQ exp
            | comp LT exp
            | comp LE exp
            | comp GT exp
            | comp GE exp'''

    op = ComparisonOp(pos(p, 2), p[2])
    p[0] = Comparison(pos(p, 2), p[1].contents + [op, p[3]])

##
### EXPRESSIONS
##

# (exp) is itself an expression. The parser handles the grouping and so on,
# so we only need to copy the expression here.
def p_exp_paren(p):
    'exp : LPAREN exp RPAREN'
    p[0] = p[2]

# Logical operators; these follow the same rule as binops, but are
# separated to make the interpreter code nicer.
def p_exp_logical(p):
    '''exp : exp OROR exp
           | exp ANDAND exp'''

    p[0] = BinaryOp(pos(p, 2), "logical", p[1], p[3], p[2])

# Comparisons are expressions
# We want them to have a lower precedence than expressions,
# see the huge comment above the precedence table.
def p_exp_comp(p):
    'exp : comp %prec CHAINCOMP'
    p[0] = p[1]

# Handle all integer types
def p_exp_num(p):
    '''exp : INT
           | HEX
           | OCT
           | BIN'''
    p[0] = Value(pos(p, 1), "int", p[1])

def p_exp_string(p):
    'exp : STRING'
    p[0] = Value(pos(p, 1), "string", p[1])

# Floats are stored differently than ints
def p_exp_float(p):
    'exp : FLOAT'
    p[0] = Value(pos(p, 1), "float", p[1])

# Identifiers can be expressions (e.g. variables); the interpreter later
# checks whether they make sense or not (since e.g. function names
# are also identifiers, and expressions like cos = 10 don't make sense).
def p_exp_ident(p):
    'exp : ident'
    p[0] = p[1]

# Function calls are expressions (their return values are, at least!)
def p_exp_call(p):
    'exp : ident LPAREN optargs RPAREN'
    p[0] = FunctionCall(pos(p, 1), p[1], p[3])

def p_optargs_none(p):
    'optargs : '
    p[0] = []

def p_optargs_args(p):
    'optargs : args'
    p[0] = p[1]

# Function arguments
def p_args_many(p):
    'args : args COMMA exp'
    p[0] = p[1] + [p[3]]

# Function arguments
def p_args_one(p):
    'args : exp'
    p[0] = [p[1]]

##
### MULTIPLE STATEMENTS
##

# Expressions can be statements. Most notably,
# the expression "xyz = 10" needs to be allowed on a line by itself,
# if followed by a semicolon (like all other statements).

def p_statements_one(p):
    'statements : statement'
    p[0] = [p[1]]

def p_statements_many(p):
    'statements : statement SEMICOLON statements'
    p[0] = [p[1]] + p[3]

def p_statements_block(p):
    'statements : block_statement statements'
    p[0] = [p[1]] + p[2]

def p_statements_empty(p):
    'statements : '
    p[0] = []

def p_block(p):
    'block : LBRACE statements RBRACE'
    p[0] = p[2]

##
### SINGLE STATEMENTS
##

def p_statement_if_if_else(p):
    '''block_statement : IF exp block else_if_blocks ELSE block
                       | IF exp block else_if_blocks'''

    def to_tree(elseifs, neither_body):
        """ Create a nested if-else tree from a list of else_if_blocks.

        For example: the p_else_if_blocks_* rules together build up a list, such that this:

        if a { a_body }
        else if b { b_body }
        else if c { c_body }
        else { neither_body }

        ... which is lexed and partially parsed to this:

        IF exp LBRACE statements RBRACE
        ELSEIF exp LBRACE statements RBRACE
        ELSEIF exp LBRACE statements RBRACE
        ELSE LBRACE statements RBRACE

        ... becomes this simple list:
        [('b', 'b_body'), ('c', 'c_body')]

        This function takes that, combined with neither_body, and eventually returns this:
        Conditional(pos, b, b_body, Conditional(c, c_body, neither_body))

        Finally, that is added to the "else" position of the partial parse tree, in the
        parent of this function.
        """

        nonlocal p

        if len(elseifs) == 0:
            return neither_body
        else:
            # TODO: the position information should really not be for p[1], but for the specific
            # TODO: else if clause
            return [Conditional(pos(p, 1), elseifs[0][0], elseifs[0][1],
                    to_tree(elseifs[1:], neither_body))]

    # If this fails, there simply was no final "else { }" block, in which case
    # we WANT last_else_block to be None.
    last_else_block = None
    try:
        last_else_block = p[6]
    except:
        pass

    else_ifs = to_tree(p[4], last_else_block)
    p[0] = Conditional(pos(p, 1), p[2], p[3], else_ifs)

# These two rules together give us, for "else if b { b_body } else if c { c_body }":
# [(b, b_body), (c, c_body)]
# That list is then used in the if statement rules above.
def p_else_if_blocks_multiple(p):
    'else_if_blocks : else_if_blocks ELSEIF exp block'
    p[0] = p[1] + [(p[3], p[4])]

def p_else_if_blocks_none(p):
    'else_if_blocks :'
    p[0] = []

# f(a, b) if x > y;
def p_single_statement_if(p):
    'statement : statement IF exp'
    p[0] = Conditional(pos(p, 2), p[3], [p[1]], None)

def p_statement_while(p):
    'block_statement : WHILE exp block'
    p[0] = While(pos(p, 1), p[2], p[3])

def p_statement_break(p):
    'statement : BREAK'
    p[0] = ControlFlowStatement(pos(p, 1), "break")

def p_statement_continue(p):
    'statement : CONTINUE'
    p[0] = ControlFlowStatement(pos(p, 1), "continue")

def p_statement_func(p):
    'block_statement : FUNC ident LPAREN optargs RPAREN block'
    p[0] = Function(pos(p, 1), p[2], p[4], p[6])

def p_statement_return(p):
    'statement : RETURN'
    p[0] = ControlFlowStatement(pos(p, 1), "return", None)

def p_statement_return_arg(p):
    'statement : RETURN exp'
    p[0] = ControlFlowStatement(pos(p, 1), "return", p[2])

def p_statement_exp(p):
    'statement : exp'
    p[0] = p[1]

##
### MISCELLANEOUS RULES
##

# Simple enough.
def p_ident(p):
    'ident : IDENT'
    p[0] = Ident(pos(p, 1), p[1])

# e.g. some_var = (2+3)^2; this is an expression that returns exp
def p_assign(p):
    'exp : ident ASSIGN exp'
    p[0] = BinaryOp(pos(p, 2), "assign", p[1], p[3], '=')
