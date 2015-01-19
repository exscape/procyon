#!/usr/bin/env python3

# See excalc-repl.py for information and such.

from excalc.interpreter import evaluate, evaluate_expr
from excalc.version import __version__, __date__, __prompt__

import sys
import re
import readline

program = """
func fac(n) {
	if n < 2 { return 1; }
	else { return n * fac(n); }
}
"""

try:
	res = evaluate(program)
	print("return from evaluate:", res)
except SyntaxError as e:
	m = re.search('input position (\d+):(\d+)$', str(e))
	if m:
		(line, pos) = (int(m.group(1)), int(m.group(2)))

		prog_line = program.split('\n')[line-1]
		print(prog_line)
		print(" " * (pos - 1) + "^")
	print("Syntax error: {}".format(str(e)))
