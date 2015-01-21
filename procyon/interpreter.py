#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

import math
import sys
import re
import codecs
from ply import lex, yacc
from .common import *  # VERSION, DATE and exceptions, mostly
import procyon.lexer as lexer
import procyon.parser as parser

__all__ = ['evaluate', 'evaluate_command', 'evaluate_file']

#
# The Procyon interpreter. Takes a string and passes it to lex and yacc,
# then interprets the syntax tree.
#

# A scope is written as a tuple, (parent_scope, {'name': val, 'name2': val2, ...})
# The global scope has None as its parent.

def decode_escapes(s):
    r""" Handle escape sequences in strings.

         On a basic level, this allows for \n to mean newline and so on, but
         it does encompass more.
         Code from: http://stackoverflow.com/a/24519338/1668576
    """

    if type(s) is not str:
        return s

    ESCAPE_SEQUENCE_RE = re.compile(r'''
        ( \\U........      # 8-digit hex escapes
        | \\u....          # 4-digit hex escapes
        | \\x..            # 2-digit hex escapes
        | \\[0-7]{1,3}     # Octal escapes
        | \\N\{[^}]+\}     # Unicode characters by name
        | \\[\\'"abfnrtv]  # Single-character escapes
        )''', re.UNICODE | re.VERBOSE)

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)

def _new_scope(cur_scope, vars, values):
    """ Create a new scope, for e.g. a function or if statement. """
    assert len(vars) == len(values)
    return (cur_scope, {k: v for k, v in zip(vars, values)})

def _var_exists(scope, var):
    """ Test if a variable exists in a given scope, or any parent/grandparent scope. """
    try:
        _read_var(scope, var)
    except ProcyonNameError:
        return False

    return True

def _read_var(scope, var):
    """ Look for a variable in the current scope.

        If it doesn't exist, look in the parent scope,
        then the grandparent scope etc.
        If not found even in the grandparent scope,
        we raise an exception.
    """

    try:
        # Try this scope first...
        return scope[1][var]
    except KeyError:
        # Well, that didn't work. What about the parent scope?
        if scope[0] is not None:
            # There is a parent scope, so let's try that.
            return _read_var(scope[0], var)
        else:
            # There is no parent scope, and we still haven't found it. Give up.
            raise ProcyonNameError('unknown identifier \"{}\"'.format(var))

def _assign_var(scope, var, value):
    """ Set a variable in a given scope. Returns the value that was assigned.

        Note that if the variable exists in a parent/grandparent scope, that variable
        is used. There is no local shadowing.
    """
    assert type(var) is str

    if var in scope[1]:
        # First, if the var exists in the local scope, use that.
        scope[1][var] = value
        return value
    elif scope[0] is not None and _var_exists(scope[0], var):
        # If it exists in some parent scope, use that var instead.
        var_scope = _scope_of_var(var, scope[0])
        assert var_scope is not None
        var_scope[1][var] = value
        return value
    else:
        # It didn't exist there, either. Create a new var in the local scope.
        scope[1][var] = value
        return value

def _scope_of_var(var, scope):
    """ Return the closest scope that contains the given variable, if any. """

    if var in scope[1]:
        # If we have this var, just return ourselves.
        return scope
    elif scope[0] is not None:
        return _scope_of_var(var, scope[0])
    else:  # ignore coverage
        return None

# def _print_all_vars(scope):
#     """ Print all variables in all scopes; first this one, then the parent, etc. """
#     for k, v in scope[1].items():
#         print("{}: {}".format(k, v))
#
#     if scope[0] is not None:
#         _print_all_vars(scope[0])

# Built-in functions and number of arguments
__functions = {'sin': 1, 'cos': 1, 'tan': 1,
               'exp': 1, 'log': 1, 'log10': 1, 'log2': 1,
               'asin': 1, 'acos': 1, 'atan': 1, 'atan2': 2,
               'sinh': 1, 'cosh': 1, 'tanh': 1,
               'asinh': 1, 'acosh': 1, 'atanh': 1,
               'abs': 1, 'sqrt': 1, 'ceil': 1, 'floor': 1,
               'trunc': 1, 'round': 2, 'print': -1, 'abort': 0}

def _init_global_state():
    global __global_scope
    __global_scope = (None, __initial_state.copy())

# Built-in constants; there are overwritable by design
__initial_state = {'e': math.e, 'pi': math.pi}
_init_global_state()

def evaluate(s, clear_state=False):
    """ Evaluate an entire program, in the form of a string. """

    if len(s.rstrip()) == 0:
        return None

    lex_lexer = lex.lex(module=lexer, debug=False, optimize=False)
    yacc_parser = yacc.yacc(module=parser, debug=True, start="toplevel")
    parse_tree = yacc_parser.parse(s, lexer=lex_lexer, debug=DEBUGPARSE)

    if DEBUGPARSE:
        print('ENTIRE TREE:', parse_tree)

    if clear_state:
        _init_global_state()

    return _evaluate_all(parse_tree, __global_scope)

def evaluate_file(filename, clear_state=False):
    """ Evaluate a program file, by reading it and passing the contents to evaluate().

    Caller is responsible for handling exceptions; both ones relating to open()/read() and
    also Procyon exceptions such as syntax errors, type errors and so on.
    """

    program = None
    with open(filename, 'r') as f:
        program = f.read()
        return evaluate(program, clear_state)

def _evaluate_all(trees, scope):
    """ Evaluate a full set of statements and return a list of results. """

    results = []
    for tree in trees:
        result = _evaluate_tree(tree, scope)
        results.append(result)
        if result is not None:
            # TODO: How should _ work? One per scope? Global only?
            # TODO: Changing in scope c also changes in each parent scope including global?
            _assign_var(scope, '_', result)

    return results

def _evaluate_tree(tree, scope):
    """ Recursively evaluate a parse tree and return the result. """

    kind = tree[0]

    if kind == "binop":
        (left_child, op, right_child) = tree[1:]
        left = _evaluate_tree(left_child, scope)
        right = _evaluate_tree(right_child, scope)

        if type(left) != type(right) and not (
                type(left) in (int, float) and type(right) in (int, float)):
            raise ProcyonTypeError("binary operation on expressions of different types:"
                                   "{} {} {}".format(left, op, right))

        if type(left) is str and type(right) is str and op != '+':
            raise ProcyonTypeError("operator {} is not defined on strings".format(op))

        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        elif op == '//':
            return left // right
        elif op == '^':
            return left ** right
        elif op == '%':
            return left % right

    elif kind == "logical":
        # && and || are a bit special in that they must use
        # short-circuit evaluation.
        # (I assume that *could* be used for other comparisons as well, but
        #  it seems more important for these.)

        (left_child, op, right_child) = tree[1:]

        left = _evaluate_tree(left_child, scope)

        # Test if we can short-circuit
        if op == '||' and left:
            return 1
        elif op == '&&' and not left:
            return 0

        # We couldn't, so we must evaluate the right side also
        right = _evaluate_tree(right_child, scope)

        # If this is an AND operation, we know the left side is true already,
        # so if the right side is true, we return 1.
        # If this is an OR operation, we know the left side is *false* already,
        # so if the right side is true, we return 1.
        return 1 if right else 0

    elif kind in ("int", "float"):
        return tree[1]

    elif kind == "string":
        return tree[1]

    elif kind == "comp":
        # chunk(['a', '>', 'b', '>=', 'c', '==', 'd']) generates the list
        # [['a', '>', 'b'], ['b', '>=', 'c'], ['c', '==', 'd']]
        # except it uses Python generators
        def chunk(l):
            for i in range(0, len(l) - 1, 2):
                yield l[i:i+3]

        def comp_one(left, op, right):
            left = _evaluate_tree(left, scope)
            right = _evaluate_tree(right, scope)
            if op == '==':
                return int(left == right)
            elif op == '!=':
                return int(left != right)
            elif op == '>':
                return int(left > right)
            elif op == '<':
                return int(left < right)
            elif op == '<=':
                return int(left <= right)
            elif op == '>=':
                return int(left >= right)
            else:  # ignore coverage
                raise ProcyonInternalError("unknown operator in comp_one")

        comparisons = tree[1]

        # ("a", ">", "b") -> [comp_one(a, >, b)]
        # ("a", ">", "b", ">=", "c") -> [comp_one(a, >, b), comp_one(b, >=, c)]
        # (Note that the above is simplified, as "a" would in reality be ("ident", "a"), etc.)
        return int(all(comp_one(*c) for c in chunk(comparisons)))

    elif kind == "uminus":
        return -_evaluate_tree(tree[1], scope)

    elif kind == "not":
        return int(not _evaluate_tree(tree[1], scope))

    elif kind == "ident":
        name = tree[1]
        if name in __functions:
            raise ProcyonTypeError("can't use built-in function \"{}\" as a variable".format(name))

        try:
            return _read_var(scope, name)
        except ProcyonNameError:
            raise ProcyonNameError('unknown identifier "{}"'.format(name))

    elif kind == "assign":
        name = tree[1][1]

        if name in __functions:
            raise ProcyonTypeError('cannot assign to built-in function "{}"'.format(name))

        val = tree[2]
        return _assign_var(scope, name, _evaluate_tree(val, scope))

    elif kind == "call":
        func_name = tree[1][1]
        args = tree[2]

        if func_name == "abort":
            # Bit of a hack, but hey... This can't really be implemented
            # as an actual function, so it has to be some sort of special case.
            raise ProcyonControlFlowException({"type": "abort"})

        if func_name not in __functions and not _var_exists(scope, func_name):
            raise ProcyonNameError('unknown function "{}"'.format(func_name))

        # OK, so it exists either as a built-in (__functions) or a user-defined function.
        # Check if it's user-defined, first:

        if _var_exists(scope, func_name):
            f = _read_var(scope, func_name)
            if type(f) is tuple and f[0] == "func":
                return _evaluate_function(f, args, scope)
            else:
                raise ProcyonTypeError('attempted to call non-function "{}"'.format(func_name))

        assert not _var_exists(scope, func_name)
        assert func_name in __functions

        # If we got here, the function is a Python function,
        # either from math, or a built-in (abs, round, print and possibly others).

        if __functions[func_name] > 0 and len(args) != __functions[func_name]:
            raise ProcyonTypeError('{} requires exactly {} arguments, {} provided'.format(
                func_name, __functions[func_name], len(args)))

        args = [_evaluate_tree(arg, scope) for arg in args]

        func = None
        try:
            func = getattr(math, func_name)
        except AttributeError:
            func = getattr(sys.modules['builtins'], func_name)

        if func == print:
            # Backslashes need some help. The string "Hello\\ \n" is printed
            # verbatim (followed by the newline print inserts), instead of
            # having a backslash, a space, and a blank line (itself ended by
            # another newline).
            print(*[decode_escapes(a) for a in args])
            return None
        else:
            return func(*args)

    elif kind == "if":
        new_scope = _new_scope(scope, [], [])
        (cond, then_body, else_body) = tree[1:]
        if _evaluate_tree(cond, scope):  # Use the old scope here!
            return _evaluate_all(then_body, new_scope)
        elif else_body:
            return _evaluate_all(else_body, new_scope)
        else:
            return None

    elif kind == "while":
        new_scope = _new_scope(scope, [], [])
        (cond, body) = tree[1:]
        while _evaluate_tree(cond, scope):  # Use the old scope here!
            try:
                _evaluate_all(body, new_scope)
            except ProcyonControlFlowException as ex:
                # I'd like to call this variable "type", but that didn't work out too well...
                # (Python's type() function stopped working elsewhere :-)
                t = ex.args[0]["type"]
                if t == "break":
                    return None
                elif t == "continue":
                    continue
                else:
                    raise  # return or abort; this is handled elsewhere
        return None

    elif kind == "break":
        raise ProcyonControlFlowException({"type": "break"})

    elif kind == "continue":
        raise ProcyonControlFlowException({"type": "continue"})

    elif kind == "func":
        # We ran across a function definition. Bind its set of statements etc. to
        # a name in the local scope.

        name = tree[1][1]
        (params, body) = tree[2:]

        _assign_var(scope, name, ("func", name, params, body))

        return None

    elif kind == "return":
        if tree[1] is not None:
            val = _evaluate_tree(tree[1], scope)
            raise ProcyonControlFlowException({"type": "return", "value": val})
        else:
            raise ProcyonControlFlowException({"type": "return", "value": None})

    raise ProcyonInternalError('reached end of _evaluate_tree! kind={}, tree: {}'.format(
        kind, tree))  # ignore coverage

# Executes a user-defined function
# Note: "args" refers to the arguments the function is passed,
# while "params" refers to the function definition's arguments.
# Example:
# func sqrt(x) { return x^(1/2); }
# sqrt(2);
# params is ["x"], while args is [2]
def _evaluate_function(func, args, scope):
    name = func[1]
    params = [p[1] for p in func[2]]
    body = func[3]

    if len(args) != len(params):
        raise ProcyonTypeError(
            'attempted to call {}() with {} argument{}, exactly {} required'.format(
                "s" if len(args) == 1 else "", name, len(args), len(params)))

    # Evaluate arguments in the *calling* scope!
    args = [_evaluate_tree(a, scope) for a in args]

    # print("...(", end="")
    # for i in range(len(args)):
    #     print("{}={}".format(params[i], args[i]), end = ", " if len(args) > i+1 else "")
    # print(")")

    func_scope = _new_scope(scope, params, args)

    try:
        _evaluate_all(body, func_scope)
    except ProcyonControlFlowException as ex:
        args = ex.args[0]
        if args["type"] == "return":
            return args["value"]
        else:
            raise  # break or continue called outside of loop, or abort()

def evaluate_command(cmd):  # ignore coverage
    """ Evaluate a command, as entered in the REPL.

        Commands are not supported for programming; they're merely
        intended as minor helpers for interactive use.
    """

    (cmd_name, *args) = re.split("\s+", cmd)

    if cmd_name == 'vars':
        # Bit of a mess... Fetch each variable name.
        # Ignore _, and ignore pre-defined constants (e.g. e, pi)
        # *UNLESS* the user has assigned other values to those names.
        # XXX: Only lists values in the global scope. This by design, at least for now;
        # commands aren't intended for use when programming, but only in the REPL.
        vars = [v for v in __global_scope[1] if (
            v != '_' and not (
                v in __initial_state and __initial_state[v] == __global_scope[1][v]))]

        for var in sorted(vars):
            print("{}:\t{}".format(var, __global_scope[1][var]))
    elif cmd_name == 'help':
        print("# Procyon REPL v" + VERSION + ", " + DATE)
        print("# Supported operators: + - * / // ^ % ( ) = == != < > >= <= && ||")
        print("# Comments begin with a hash sign, as these lines do.")
        print("# = assigns, == tests equality (!= tests non-equality), e.g.:")
        print("# a = 5")
        print("# a == 5 # returns 1 (true)")
        print("#")
        print("# Supported commands (in the REPL only):")
        print("# .help - this text")
        print("# .vars - show all variables, except non-modified builtins")
        print("# .import <file.pr> - interpret a file, making its functions/variables available")
        print("#")
        print("# Built-in functions (number of arguments, if not 1):")
        print("# " + ", ".join(sorted(["{}{}".format(f, "({})".format(
            __functions[f]) if __functions[f] > 1 else "") for f in __functions])))
        print("#")
        print("# Built-in constants (names are re-assignable):")
        print("# " + ", ".join(sorted(__initial_state)))
        print("# Use _ to access the last result, e.g. 12 + 2 ; _ + 1 == 15 # returns True")
        print("# Use 0x1af, 0o175, 0b11001 etc. to specify hexadecimal/octal/binary numbers.")
        print("# See README.md for more information.")
    elif cmd_name == 'import':
        if len(args) == 1:
            evaluate_file(args[0])
        else:
            print("Usage: .import <file.py>")
    else:
        raise ProcyonNameError("unknown command {}".format(cmd_name))
