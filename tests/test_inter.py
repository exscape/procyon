# Requires pytest; install with "pip install pytest" (as root) if pip is available

# vim: ts=4 sts=4 et sw=4

import pytest
from tests_common import ev, ev_reuse_state

#
# Test functions
#

def test_functions():
    prog = "func sqr(x) { return x*x; } sqr(-1); sqr(0); sqr(2); sqr(-4); sqr(10);"
    assert ev(prog)[-5:] == [1, 0, 4, 16, 100]
    prog = "func sqr(x) { return x*x } sqr(-1); sqr(0); sqr(2); sqr(-4); sqr(10)"
    assert ev(prog)[-5:] == [1, 0, 4, 16, 100]

def test_function_args():
    prog = "func zero() { return 0; } zero();"
    assert ev(prog)[-1] == 0
    prog = "func one(x) { return x; } one(1);"
    assert ev(prog)[-1] == 1
    prog = "func two(x,y) { return x + y; } two(1,2);"
    assert ev(prog)[-1] == 3

def test_function_wrong_args():
    prog = "func one(x) { return x; } one();"
    with pytest.raises(TypeError):
        ev(prog)
    prog = "func one(x) { return x; } one(1,2);"
    with pytest.raises(TypeError):
        ev(prog)
    prog = "func one(x) { return x; } one(1,2,3);"
    with pytest.raises(TypeError):
        ev(prog)

def test_nested_functions():
    prog = """
    func pow_3_2(x) {
        func pow_3(x) { return x^3; }
        func pow_1_2(x) { return x^(1/2); }
        return pow_1_2(pow_3(x));
    }
    pow_3_2(1); pow_3_2(100); pow_3_2(10000);
    """
    assert ev(prog)[-3:] == [1, 1000, 1000000]

def test_nested_functions_fail():
    prog = """
    func pow_3_2(x) {
        func pow_3(x) { return x^3; }
        func pow_1_2(x) { return x^(1/2); }
        return pow_1_2(pow_3(x));
    }
    pow_3(10);
    """
    with pytest.raises(NameError):
        ev(prog)

#
# Test strings
#

def test_string_1(capsys):
    prog = """
    s = "Hello, world!";
    print(s);
    """
    assert ev(prog)[-1] is None
    assert capsys.readouterr()[0] == "Hello, world!\n"

def test_string_2(capsys):
    prog = r"""
    print("line 1\nline 2\n\nline 4");
    """
    assert ev(prog)[-1] is None
    assert capsys.readouterr()[0] == "line 1\nline 2\n\nline 4\n"

def test_string_3(capsys):
    prog = r"""
    print("\n\\\n");
    """
    assert ev(prog)[-1] is None
    assert capsys.readouterr()[0] == "\n\\\n\n"

def test_string_4(capsys):
    prog = r"""
    s = "Woo-\"";
    s2 = "! \"Escaped\" quotes!";
    print (s + "hoo\"" + s2);
    """
    assert ev(prog)[-1] is None
    assert capsys.readouterr()[0] == "Woo-\"hoo\"! \"Escaped\" quotes!\n"

def test_string_fail_1():
    prog = """ print(4 + "abc"); """
    with pytest.raises(TypeError):
        ev(prog)

def test_string_fail_2():
    prog = """ print("abc" - "def"); """
    with pytest.raises(TypeError):
        ev(prog)


#
# Test returns (void returns; regular ones are tested in many other places)
#

def test_void_return():
    prog = """
    x = 10;
    func noret(x) { x = x^2; return; }
    y = noret(x);
    x;
    y;
    """
    assert ev(prog)[-3:] == [None, 10, None]

#
# Test if/else statements
#

def test_if_1():
    prog = """
    x = 0;
    y = 12;
    if y > 5 {
        x = 2;
    }
    x;
    """
    assert ev(prog)[-1] == 2

def test_if_2():
    prog = """
    x = 0;
    y = 5;
    if y^2 - 5 > 22 {
        x = 2;
    }
    else {
        x = 1;
    }
    x;

    """
    assert ev(prog)[-1] == 1

def test_if_nested():
    prog = """
    y = 0;
    if x = 2^3 > 7 {
        y = y + 1;
        if x {
            y = y + 1;
        }
        else {
            y = 100;
        }
    }
    else {
        y = 200;
    }
    y;
    """
    assert ev(prog)[-1] == 2

def test_if_func():
    prog = """
    x = 0;
    func sqr(x) { return x*x; }
    if sqr(10) == 100 {
        func p(x) { print(x); return x; }
        x = p(25);
    }
    x;
    """
    assert ev(prog)[-1] == 25

def test_if_scope_fail():
    prog = """
    func sqr(x) { return x*x; }
    if sqr(10) == 100 {
        func p(x) { print(x); return x; }
        x = p(25);
    }
    x = p(50);
    """
    with pytest.raises(NameError):
        ev(prog)

#
# Test variable scoping
#

def test_scoping_1():
    prog = "v = 10; if (v > 5) { v = 15; } v;"
    assert ev(prog)[-1] == 15
    prog = "v = 10; func f() { v = 15; return v; } f(); v;"
    assert ev(prog)[-2:] == [15, 15]

def test_scoping_2():
    prog = "v = 10; func f() { a = 5; return a; } f(); v;"
    assert ev(prog)[-2:] == [5, 10]

def test_scoping_3():
    prog = """
    v = 10;
    func f(x) {
        b = 0;
        if x > 5 {
            v = 5;
            b = 1;
        }
        else {
            v = 7;
            b = 2;
        }
        return b;
    }
    f(6);
    v;
    """
    assert ev(prog)[-2:] == [1, 5]

def test_scoping_4():
    prog = """
    x = 5;
    func test(x) {
        return x;
    }
    x;
    test(12);
    x;
    """
    assert ev(prog)[-3:] == [5, 12, 5]

def test_scoping_fail_1():
    prog = """
    if (5 > 4) {
        xyz = 10;
    }
    print(xyz);
    """
    with pytest.raises(NameError):
        ev(prog)

def test_scoping_fail_2():
    prog = """
    func test(x, y) {
        if (x > y) {
            z = x*y;
        }
        else {
            z = x+y;
        }
        return z;
    }
    test(12, 4);
    """
    with pytest.raises(NameError):
        ev(prog)

#
# Test short-circuit evaluation
#

def test_short_circuit_or():
    header = """
    err = 0;
    func s() { err = 1; return 1; } # Should never run
    """
    footer = "; err;"

    tests = ["1 || s()",
             "0 || 1 || s()",
             "(0 || 1) || s() || 3",
             "!!(3+4) || s()",
             "!(5 > 4 >= 10) || s()"]
    for test in tests:
        prog = header + test + footer
        assert ev(prog)[-1] == 0  # Test that err == 0

def test_short_circuit_and():
    header = """
    err = 0;
    func s() { err = 1; return 1; } # Should never run
    """
    footer = "; err;"

    tests = ["0 && s()",
             "1 && 0 && s()",
             "(1 && 0) && s()",
             "!10 && s()",
             "(0 && s()) && s()"]
    for test in tests:
        prog = header + test + footer
        assert ev(prog)[-1] == 0  # Test that err == 0

def test_short_circuit_misc():
    header = """
    err = 1;
    func s() { err = 0; return 1; } # Should ALWAYS run
    """
    footer = "; err;"

    tests = ["1 && 2 && s() && 0",
             "0 || 1 && s() && 2",
             "s() && 0",
             "s() && 1",
             "(0 || s()) && 0",
             "(0 || s()) && 1"]
    for test in tests:
        prog = header + test + footer
        assert ev(prog)[-1] == 0  # Test that err == 0
