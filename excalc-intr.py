#!/usr/bin/env python3

# vim: ts=4 sts=4 et sw=4

# See excalc-repl.py for information and such.

from excalc.interpreter import evaluate, evaluate_expr
from excalc.version import __version__, __date__, __prompt__

import sys
import re
import readline

program = """
loops = 0;
func fac(n) {
    loops = loops + 1;
    func test(x) { print("Nested function says:", x); }
    if n < 2 { return 1; }
    else { test(n); return n * fac(n - 1); }
}

print("fac(5) =", fac(5));
print("number of loops:", loops);
"""

# program = """
# x = 4;
# y = 2;
# if x > 3 {
#     print("Setting y to some value");
#     y = x^2 + 1 - sin(x)^2;
# }
# else {
#     print("Setting y to 5");
#     y = 5;
# }
# print("The value of y is", y);
# """

# print(program.strip())
# print('---------------------------------')

try:
    res = evaluate(program)
    #print("return from evaluate:", res)
except SyntaxError as e:
    m = re.search('input position (\d+):(\d+)$', str(e))
    if m:
        (line, pos) = (int(m.group(1)), int(m.group(2)))

        prog_line = program.split('\n')[line-1]
        print(prog_line)
        print(" " * (pos - 1) + "^")
    print("Syntax error: {}".format(str(e)))
except RuntimeError as e:
    print(str(e))

### HIGH PRIORITY TODO ITEMS:
# TODO: Look through all exceptions and change them (esp. SyntaxError) for more fitting ones
# TODO: Write tests that use functions, if statements, scoping and more
# TODO: Verify test coverage with cov

### Lower priority:

### TODO: Support reading programs from files (via sys.argv to this program)
### TODO: test ^ error pointing with comments
### TODO: fix ^ pointing with tab indentation
### TODO: catch all possible exceptions in the interpreter
