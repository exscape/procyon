# vim: ts=4 sts=4 et sw=4

import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from procyon import evaluate
from procyon import evaluate_command

def ev(*args):
    """ Evaluate a string with a fresh global state.

    This is important to ensure that test results are independent on prior tests.
    For example, a variable that shouldn't exist due to scoping may exist from a
    prior test.
    """
    return evaluate(*args, clear_state=True)

def ev_reuse_state(*args):
    """ Evaluate a string with the previous state.

    Useful for some tests, but not a majority.
    """
    return evaluate(*args, clear_state=False)

def ev_command(*args):
    return evaluate_command(*args)
