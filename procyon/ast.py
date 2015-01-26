#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

#
# Classes used to represent the Procyon AST.
# Used mostly by the parser and interpreter modules.
#

class Node:
    pass

class Value(Node):
    """ Represents a value of some kind, such as int, float and string. """
    def __init__(self, pos, kind, value):
        assert kind in ("int", "float", "string")
        self.pos = pos
        self.kind = kind
        self.value = value

    def __repr__(self):
        return repr(self.value)

class Ident(Node):
    """ Represents a variable. """
    def __init__(self, pos, name):
        self.pos = pos
        self.name = name

    def __repr__(self):
        return "(ident: {})".format(self.name)

class BinaryOp(Node):
    """ Represents all operations with a left side, an operator, and a right side.

        Comparisons are excluded, because they need to follow different rules,
        and do not even always HAVE a left side and a right side. See Comparison below.

        a - b - c is ((a - b) - c), but a == b == c is NOT ((a == b) == c).
        In the example above,
        a == b is a comparison which returns 0 or 1, which is tested against c.
        However, without the parenthesis,
        a == b == c is a comparison that returns 0 or 1 if all three variables have
        the same value.

        Kinds:
        "math": +, -, *, /, ^, //, %
        "logical": &&, ||
        "assign": =
    """

    def __init__(self, pos, kind, left, right, op=None):
        assert kind in ("math", "logical", "assign")
        self.pos = pos
        self.kind = kind
        if kind == "assign":
            assert isinstance(left, Ident)  # The parser rules should take care of this
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return "(binop: {} {} {})".format(self.left, self.op, self.right)

class Comparison(Node):
    """ Represents a comparison, possibly between more than two values.

    a > b >= c == d is stored as a single comparison, with "contents" being
    [a, >, b, >=, c, ==, d] (where each value really is a Node instance of some kind).
    """

    def __init__(self, pos, contents):
        self.pos = pos
        self.contents = contents

    def __repr__(self):
        return "(comp: " + " ".join([str(x) for x in self.contents]) + ")"

class ComparisonOp(Node):
    """ Represents a single comparison operator.

    BinaryOp is not used to avoid confusion; if that WAS used, the left+right sides would have
    to be set, but ignored; comparisons don't have left/right sides, since they can be
    comprised of multiple comparison operators.
    """

    def __init__(self, pos, op):
        self.pos = pos
        self.op = op

    def __repr__(self):
        return str(self.op)

class UnaryOp(Node):
    """ Represents a unary operation, such as !arg and -arg. """
    def __init__(self, pos, op, arg):
        assert op in ('-', '!')
        self.pos = pos
        self.op = op
        self.arg = arg

    def __repr__(self):
        return "{}{}".format(self.op, self.arg)

class Function(Node):
    """ Represents a function definition. """
    def __init__(self, pos, name, params, body):
        self.pos = pos
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        params = [repr(a) for a in self.params]
        return "func {}({}) {}".format(self.name, ", ".join(params), self.body)

class Conditional(Node):
    """ Represents an if or if-else clause. """
    def __init__(self, pos, cond, then_body, else_body):
        self.pos = pos
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

    def __repr__(self):
        if self.else_body:
            return "if ({}) {} else {}".format(self.cond, self.then_body, self.else_body)
        else:
            return "if ({}) {}".format(self.cond, self.then_body)

class While(Node):
    """ Represents a while loop. """
    def __init__(self, pos, cond, body):
        self.pos = pos
        self.cond = cond
        self.body = body

    def __repr__(self):
        return "while ({}) {}".format(self.cond, self.body)

class FunctionCall(Node):
    """ Represents a function call. """
    def __init__(self, pos, func_name, args):
        self.pos = pos
        self.func_name = func_name
        self.args = args

    def __repr__(self):
        args = [repr(a) for a in self.args]
        return "(call: {}, [{}])".format(self.func_name, ", ".join(args))

class ControlFlowStatement(Node):
    """ break, continue or return; only return may have arguments. """
    def __init__(self, pos, kind, arg=None):
        assert kind in ("break", "continue", "return")
        if arg:
            assert kind == "return"
        self.pos = pos
        self.kind = kind
        self.arg = arg

    def __repr__(self):
        if self.arg:
            return "{} {}".format(self.kind, self.arg)
        else:
            return self.kind
