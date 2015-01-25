# Requires pytest; install with "pip install pytest" (as root) if pip is available

# vim: ts=4 sts=4 et sw=4

#
# A few tests of programs that are more realistic than the other tests.
# I find it difficult to come up with good, non-contrived tests,
# so I figured: why not write a few tests that I've actually written for real
# in other languages?
# That way, I also get an idea of what language features are most urgent to add.
#

import pytest
import tests_common  # Note: this import is necessary for the procyon imports to work
from procyon.interpreter import evaluate_file
from procyon.common import *  # Mostly exceptions

def euler(n):
    res = evaluate_file('tests/euler/{}.pr'.format(n))
    return res[-1]

def test_euler_1():
    assert euler(1) == 233168

def test_euler_2():
    assert euler(2) == 4613732

def test_euler_3():
    res = euler(3)
    assert res == 6857
    assert type(res) is int
