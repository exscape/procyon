#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

import math
import sys
from ply import lex, yacc
from .common import *  # decode_escapes, VERSION, DATE and exceptions, mostly
from . import lexer, parser
from .ast import (Node, Value, Ident, BinaryOp, UnaryOp, Function, Conditional,
                  While, FunctionCall, ControlFlowStatement, Comparison, ComparisonOp)

__all__ = ['evaluate', 'evaluate_command', 'evaluate_file']

#
# The Procyon interpreter. Takes a string and passes it to lex and yacc,
# then interprets the syntax tree.
#

# (A Brief History of) Scoping rules in Procyon
#
# Originally, just as functions and if-statements were added, the scoping rules were quite simple:
# A new scope was created for each set of braces, whether they were for a function, a conditional,
# or a loop.
# When reading a variable, the local scope was checked first. If it was not present there,
# the outer scope was checked. If not there, either, the next outer scope was checked, and so on,
# until the global scope had been checked unsuccessfully, at which point a NameError was raised.
#
# For writing, a similar approach was used. If the variable existed in the local scope, that one
# was used. If not, outer scopes were checked recursively. If it didn't exist in any of those,
# one was created in the local scope.
#
# This turned out to be problematic. Most notably, using a variable (such as "i" for a loop counter)
# inside a function *and* in the main program (i.e. in the global scope) had unintended
# consequences, since calling a function that modifies "i" inside a loop will alter the local
# loop variable as well, often causing infinite looping.
#
# A better approach was required. Simply requiring a keyword/sigil to access non-local scopes
# sounds fairly good, until one realizes that if-statements are scopes, so it would be impossible
# to change a variable inside an if-statement; it'd only change inside that if block... unless
# all variables used such sigils, meaning ALL variables are globals.
#
# I chose to solve this similarly to how Python works -- after embarrasingly realize I didn't
# understand Python scoping rules prior to now. The following code DOES work in Python:
#
# if something:
#     x = 1
# print(x)
#
# ... even if that is the entire program. I would have expected, and have always coded as if,
# that would yield a NameError from the x only existing in the if scope -- but it turns out
# if-statements do not CREATE new scopes... so I chose a similar behavior for Procyon.
#
# The language works like this:
# When reading a variable, the local (i.e. closest function) scope is tested first.
# If not present there, the outer scope is checked, and so on, until we reach the outermost
# scope (the global scope). If not found in any of those, a ProcyonNameError is raised.
# So far, so good. This makes nested functions work properly, without any hacks.
#
# When assigning, the rules are different. If the variable already exists in the local scope, that
# one is used. If not, a new variable is created in the local scope. Outer scopes are never
# checked, and never written to, so that function cannot accidentally affect other functions or
# the global scope.
#
# Sometimes it may be desirable to use global variables. In that case, we can use a special
# keyword or sigil to denote it as such (as Python uses "global" and Ruby uses the $ sigil).
# Such a variable is denoted by a $ sigil in Procyon; they can be read (and written) from ANY scope,
# and ignore all scoping rules.
# For example, they can be defined inside a block itself inside a nested function), yet be accessed
# from the global scope, as long as the access from the global scope occurs later in the
# interpretation process.

# A scope is written as a tuple, (outer/parent scope, {'name': val, 'name2': val2, ...})
# The global scope has None as its parent.

def _new_scope(cur_scope, vars, values):
    """ Create a new scope, for e.g. a function. """
    assert len(vars) == len(values)
    return (cur_scope, {k: v for k, v in zip(vars, values)})

def _var_exists(scope, var):
    """ Test if a variable exists in a given scope, or (recursively) in any outer scope. """
    try:
        _read_var(scope, var)
    except ProcyonNameError:
        return False

    return True

def _read_var(scope, var):
    """ Look for a variable in the current scope, and if found, return its value.

        If it doesn't exist, look in the outer scope, then the next outer scope,
        and so on. If not found even in the global scope, we raise an exception.

        Variables that begin with a $ are globals, and are treated differently:
        they are simply stored in the global scope.
    """

    name = var.name

    if name[0] == '$':
        try:
            return __global_scope[1][name]
        except KeyError:
            raise ProcyonNameError(var.pos, 'unknown identifier "{}"'.format(name))
    else:
        try:
            # Try this scope first...
            return scope[1][name]
        except KeyError:
            # Well, that didn't work. What about the outer/parent scope?
            if scope[0] is not None:
                # There is a parent scope, so let's try that.
                return _read_var(scope[0], var)
            else:
                # There is no parent scope, and we still haven't found it. Give up.
                raise ProcyonNameError(var.pos, 'unknown identifier "{}"'.format(name))

def _assign_var(scope, var, value):
    """ Set a variable in a given scope. Returns the value that was assigned.

        If the same variable exists in an outer (parent/grandparent/...) scope,
        that one is shadowed by the local one! Only global variables ($name)
        can modify values in outside scopes.

        Global variables are stored in the global scope, regardless of where
        the assignment happens (e.g. an assignment from inside a nested function
        can be later accessed by the global scope).
    """

    if var[0] == '$':
        __global_scope[1][var] = value
        return value
    else:
        scope[1][var] = value
        return value

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
               'trunc': 1, 'round': 2, 'print': -1, 'abort': 0,
               'input_str': 1, 'input_int': 1, 'input_float': 1}

def _init_global_scope():
    global __global_scope
    __global_scope = (None, __initial_state.copy())

# Built-in constants; these are overwritable by design
__initial_state = {'e': math.e, 'pi': math.pi}
_init_global_scope()

def evaluate(s, clear_state=False, last=None):
    """ Evaluate an entire program, in the form of a string.

    Keyword arguments:
    clear_state -- if True, the interpreter state is reset prior to evaluating the program
    last -- the value to assign to the _ variable throughout the evaluation of the entire program
    """

    if len(s.rstrip()) == 0:
        return None

    lex_lexer = lex.lex(module=lexer, debug=False, optimize=False)
    yacc_parser = yacc.yacc(module=parser, debug=True, start="toplevel")
    parse_tree = yacc_parser.parse(s, lexer=lex_lexer, debug=DEBUGPARSE)

    if DEBUGPARSE:
        # Yep, this is (up to) 200 chars wide!
        # Semi-complex parse trees are unreadable at 100 chars or less, so
        # I figure "why not?". Fits on a single 1080p monitor. Resizing a terminal
        # isn't that difficult. :-)
        import pprint
        print("Parse tree:")
        tstr = pprint.pformat(parse_tree, indent=4, width=200)
        max_len = max([len(line) for line in tstr.split('\n')])
        print("-" * max_len)
        print(tstr)
        print("-" * max_len)

    if clear_state:
        _init_global_scope()

    if last:  # ignore coverage
        # This is only used in the REPL, which isn't automatically tested.
        __global_scope[1]['_'] = last

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

    return [_evaluate_tree(tree, scope) for tree in trees]

def _evaluate_tree(tree, scope):
    """ Recursively evaluate a parse tree and return the result. """

    if isinstance(tree, BinaryOp):
        if tree.kind == 'math':
            left_child, op, right_child = tree.left, tree.op, tree.right
            left = _evaluate_tree(left_child, scope)
            right = _evaluate_tree(right_child, scope)

            if type(left) != type(right) and not (
                    type(left) in (int, float) and type(right) in (int, float)):
                raise ProcyonTypeError(
                    tree.pos, "binary operation on expressions of different types: "
                    "{} {} {}".format(left, op, right))

            if type(left) is str and type(right) is str and op != '+':
                raise ProcyonTypeError(tree.pos, "operator {} is not defined on strings".format(op))

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

        elif tree.kind == "logical":
            # && and || are a bit special in that they must use
            # short-circuit evaluation.
            # (I assume that *could* be used for other comparisons as well, but
            #  it seems more important for these.)

            left_child, op, right_child = tree.left, tree.op, tree.right

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

        elif tree.kind == "assign":
            name = tree.left.name

            if name in __functions:
                raise ProcyonTypeError(
                    tree.left.pos, 'cannot assign to built-in function "{}"'.format(name))

            val = tree.right
            return _assign_var(scope, name, _evaluate_tree(val, scope))

    elif isinstance(tree, UnaryOp):
        if tree.op == '-':
            return -_evaluate_tree(tree.arg, scope)
        elif tree.op == '!':
            return int(not _evaluate_tree(tree.arg, scope))

    elif isinstance(tree, Value):
        # kind does not matter, we want to return the value in all cases
        return tree.value

    elif isinstance(tree, Comparison):
        # chunk(['a', '>', 'b', '>=', 'c', '==', 'd']) generates the list
        # [['a', '>', 'b'], ['b', '>=', 'c'], ['c', '==', 'd']]
        # except it uses Python generators
        def chunk(l):
            for i in range(0, len(l) - 1, 2):
                yield l[i:i+3]

        def comp_one(left_tree, op_node, right_tree):
            left = _evaluate_tree(left_tree, scope)
            right = _evaluate_tree(right_tree, scope)

            if type(left) != type(right) and not (
                    type(left) in (int, float) and type(right) in (int, float)):
                raise ProcyonTypeError(
                    op_node.pos, "comparison between incompatible types: "
                    "{} {} {}".format(left, op_node.op, right))

            op = op_node.op

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
            else:
                raise ProcyonInternalError("unknown operator in comp_one")

        # ("a", ">", "b") -> [comp_one(a, >, b)]
        # ("a", ">", "b", ">=", "c") -> [comp_one(a, >, b), comp_one(b, >=, c)]
        return int(all(comp_one(*c) for c in chunk(tree.contents)))

    elif isinstance(tree, Ident):
        if tree.name in __functions:
            raise ProcyonTypeError(
                tree.pos, "can't use built-in function \"{}\" as a variable".format(tree.name))

        try:
            return _read_var(scope, tree)
        except ProcyonNameError:
            raise ProcyonNameError(tree.pos, 'unknown identifier "{}"'.format(tree.name))

    elif isinstance(tree, FunctionCall):
        func_ident = tree.func_name
        func_name = func_ident.name
        args = tree.args

        if func_name == "abort":
            # Bit of a hack, but hey... This can't really be implemented
            # as an actual function, so it has to be some sort of special case.
            raise ProcyonControlFlowException(func_ident.pos, {"type": "abort"})

        if func_name not in __functions and not _var_exists(scope, func_ident):
            raise ProcyonNameError(func_ident.pos, 'unknown function "{}"'.format(func_name))

        # OK, so it exists either as a built-in (__functions) or a user-defined function.
        # Check if it's user-defined, first:

        if _var_exists(scope, func_ident):
            f = _read_var(scope, func_ident)
            if isinstance(f, Function):
                return _evaluate_function(f, args, scope)
            else:
                raise ProcyonTypeError(
                    func_ident.pos, 'attempted to call non-function "{}"'.format(func_name))

        assert not _var_exists(scope, func_ident)
        assert func_name in __functions

        # If we got here, the function is a Python function,
        # either from math, or a built-in (abs, round, print and possibly others).

        if __functions[func_name] > 0 and len(args) != __functions[func_name]:
            raise ProcyonTypeError(
                func_ident.pos, '{} requires exactly {} arguments, {} provided'.format(
                    func_name, __functions[func_name], len(args)))

        args = [_evaluate_tree(arg, scope) for arg in args]

        if func_name in ('input_str', 'input_int', 'input_float'):
            return _handle_input(func_ident, args[0])  # ignore coverage

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

    elif isinstance(tree, Conditional):
        # NOTE: if statements (and loops) do NOT create new scopes.
        # The closest function's scope is used, so creating a variable
        # inside an if block and later using it outside is fine.
        if _evaluate_tree(tree.cond, scope):
            _evaluate_all(tree.then_body, scope)
        elif tree.else_body:
            _evaluate_all(tree.else_body, scope)

        return None

    elif isinstance(tree, While):
        while _evaluate_tree(tree.cond, scope):
            try:
                _evaluate_all(tree.body, scope)
            except ProcyonControlFlowException as ex:
                # I'd like to call this variable "type", but that didn't work out too well...
                # (Python's type() function stopped working elsewhere :-)
                t = ex.args[1]["type"]
                if t == "break":
                    return None
                elif t == "continue":
                    continue
                else:
                    raise  # return or abort; this is handled elsewhere

        return None

    elif isinstance(tree, ControlFlowStatement):
        if tree.kind in ("break", "continue"):
            raise ProcyonControlFlowException(tree.pos, {"type": tree.kind})
        elif tree.kind == "return":
            if tree.arg is not None:
                val = _evaluate_tree(tree.arg, scope)
                raise ProcyonControlFlowException(tree.pos, {"type": "return", "value": val})
            else:
                raise ProcyonControlFlowException(tree.pos, {"type": "return", "value": None})

    elif isinstance(tree, Function):
        # We ran across a function definition. Bind its set of statements etc. to
        # a name in the local scope.
        name = tree.name.name

        if name in __functions:
            raise ProcyonTypeError(
                tree.name.pos, 'cannot ovewrite built-in function "{}"'.format(name))

        _assign_var(scope, name, tree)

        return None

    raise ProcyonInternalError('reached end of _evaluate_tree! kind={}, tree: {}'.format(
        kind, tree))

# Executes a user-defined function
# Note: "args" refers to the arguments the function is passed,
# while "params" refers to the function definition's arguments.
# Example:
# func sqrt(x) { return x^(1/2); }
# sqrt(2);
# params is ["x"], while args is [2]
def _evaluate_function(func, args, scope):
    name = func.name
    params = [p.name for p in func.params]
    body = func.body

    if len(args) != len(params):
        raise ProcyonTypeError(
            name.pos, 'attempted to call {}() with {} argument{}, exactly {} required'.format(
                name, len(args), "s" if len(args) != 1 else "", len(params)))

    # Evaluate arguments in the *calling* scope!
    args = [_evaluate_tree(a, scope) for a in args]

    try:
        func_scope = _new_scope(scope, params, args)
        _evaluate_all(body, func_scope)
    except ProcyonControlFlowException as ex:
        args = ex.args[1]
        if args["type"] == "return":
            return args["value"]
        else:
            raise  # break or continue called outside of loop, or abort()

def _handle_input(func, prompt):
    """ Handle input_* calls (int, float and str). """

    type_ = func.name[6:]
    val = input(prompt)

    if type_ == 'float':
        try:
            return float(val)
        except ValueError:
            raise ProcyonTypeError(func.pos, "user-entered string is not a valid float")
    elif type_ == 'int':
        try:
            return int(val)
        except ValueError:
            raise ProcyonTypeError(func.pos, "user-entered string is not a valid int")
    else:
        assert type_ == 'str'
        return val

def evaluate_command(cmd):  # ignore coverage
    """ Evaluate a command, as entered in the REPL.

        Commands are not supported for programming; they're merely
        intended as minor helpers for interactive use.
    """

    (cmd_name, *args) = re.split(r'\s+', cmd)

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
        print("# Use _ to access the last result.")
        print("# Use 0x1af, 0o175, 0b11001 etc. to specify hexadecimal/octal/binary numbers.")
        print("# See README.md for more information.")

    elif cmd_name == 'import':
        if len(args) == 1:
            evaluate_file(args[0])
        else:
            print("Usage: .import <file.py>")

    else:
        raise ProcyonNameError((-1, -1), "unknown command {}".format(cmd_name))
