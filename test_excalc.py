# Requires pytest; install with "pip install pytest" (as root) if pip is available

import pytest
from excalc import evaluate as ev

def test_empty():
	assert ev("") == None

def test_single():
	assert ev("1") == [1]
	assert ev("_") == [1]

def test_addition():
	assert ev("1+1") == [2]
	assert ev("4+3") == [7]
	assert ev("1+2+3") == [6]

def test_subtraction():
	assert ev("1-1") == [0]
	assert ev("1-2-3") == [-4]
	assert ev("120-5-3-6") == [106]

def test_multiplication():
	assert ev("0*100") == [0]
	assert ev("10*100") == [1000]
	assert ev("5*4*3") == [60]

def test_division():
	assert ev("0*100") == [0]
	assert ev("10*100") == [1000]
	assert ev("5*4*3") == [60]

def test_exponentiation():
	assert ev("2^3") == [8]
	assert ev("3^0") == [1]
	assert ev("2^-2") == [0.25]
	assert ev("2^(-2)") == [0.25]

def test_floats():
	# We need to be careful here, since we test equality. 1/10 won't yield exactly 0.1,
	# but 1/8 *will* yield exactly 0.125. We'll have to stick to number that are nice
	# in binary.
	assert ev("1/4") == [0.25]
	assert ev("25/4") == [6.25]
	assert ev("14.4375/3") == [4.8125]

def test_float_exp():
	assert ev("2.3e3") == [2300]
	assert ev("1.25e-2") == [0.0125]
	assert ev("1.23e6") == [1230000]

def test_precedence():
	assert ev("1+2*3^2") == [19]
	assert ev("10+4*4/2") == [18]
	assert ev("(1+2*3)^2") == [49]
	assert ev("1+(2*3)^2") == [37]

def test_parenthesis():
	assert ev("(1)") == [1]
	assert ev("((1))") == [1]
	assert ev("(1+2)^3") == [27]
	assert ev("(1+2+3)*4") == [24]

def test_associativity():
	assert ev("1-2-3") == [-4]
	assert ev("(1-2)-3") == [-4]
	assert ev("1-(2-3)") == [2]

	assert ev("4^3^2") == [4**9]
	assert ev("-2^4") == [-16]
	assert ev("-(2^4)") == [-16]
	assert ev("(-2)^4") == [16]

def test_hex():
	assert ev("0x0") == [0]
	assert ev("0x9") == [9]
	assert ev("0xa") == [10]
	assert ev("0x10") == [16]
	assert ev("0xff") == [255]
	assert ev("0x7fa4") == [32676]

def test_oct():
	assert ev("0o0") == [0]
	assert ev("0o5") == [5]
	assert ev("0o10") == [8]
	assert ev("0o20") == [16]
	assert ev("0o755") == [493]

def test_bin():
	assert ev("0b0") == [0]
	assert ev("0b01") == [1]
	assert ev("0b1") == [1]
	assert ev("0b0001110") == [14]
	assert ev("0b1111") == [15]

def test_uminus():
	assert ev("-1") == [-1]
	assert ev("-(4+2)") == [-6]
	assert ev("-(2-4)") == [2]
	assert ev("-2^3") == [-8]
	assert ev("-(2^3)") == [-8]

def test_multiple():
	assert ev("5+2; (1+2)^3; sqrt(100)") == [7, 27, 10]
	assert ev("5+2; (1+2)^3; sqrt(100);") == [7, 27, 10]
	assert ev("10+5;") == [15]
	assert ev("10+5; 2^3") == [15, 8]

def test_comparisons_1():
	assert ev("5 > 4") == [1]
	assert ev("5 > 5") == [0]
	assert ev("5 >= 5") == [1]
	assert ev("5 > 4 > 3") == [1]
	assert ev("5 > 4 > 3 >= 2 == 2") == [1]
	assert ev("7 > 4 < 6 == 6") == [1]

def test_comparisons_2():
	assert ev("(5 > 4) > 1") == [0]
	assert ev("(5 > 4) == 1") == [1]
	assert ev("(5 > 4 > 3) == 1") == [1]
	assert ev("1 == (5 > 4)") == [1]
	assert ev("1 == ((10 >= 10) == 1)") == [1]
	assert ev("0 != (4 <= 5)") == [1]

def test_comparisons_3():
	assert ev("10 == (a=10) == 10") == [1]
	assert ev("1 == a = 10 == 10") == [1]
	assert ev("1 == (6 > 4 >= 4 < 6 == 6)") == [1]
	assert ev("0 != (5 > 4 == 4)") == [1]
	assert ev("4 == (!(4^2<3) + 3) == 4") == [1]
	assert ev("!!2^4 >= 0 > -(2^3) == -8") == [1]
	assert ev("((34 == 30 + 4) == 1) == 0") == [0]

def test_syntax_error_1():
	with pytest.raises(SyntaxError):
		ev("1+3+(4))")

def test_syntax_error_2():
	with pytest.raises(SyntaxError):
		ev("1+(3+(4)")

def test_syntax_error_3():
	with pytest.raises(SyntaxError):
		ev("sin")

def test_syntax_error_4():
	with pytest.raises(SyntaxError):
		ev("cos()")

def test_syntax_error_5():
	with pytest.raises(SyntaxError):
		ev("cos(3, 2)")

def test_syntax_error_6():
	with pytest.raises(SyntaxError):
		ev("2^3!")

def test_syntax_error_7():
	with pytest.raises(SyntaxError):
		ev("10 + 3 + 5%")

def test_syntax_error_8():
	with pytest.raises(SyntaxError):
		ev(".hello")

def test_syntax_error_9():
	with pytest.raises(SyntaxError):
		ev("sin(1) = 3")

def test_keyerror_1():
	with pytest.raises(KeyError):
		ev("5 + abc")

def test_keyerror_2():
	with pytest.raises(KeyError):
		ev("sin = 40")

def test_not():
	assert ev("!1") == [0]
	assert ev("!0") == [1]
	assert ev("!!1") == [1]
	assert ev("!!(12 + 4)") == [1]
	assert ev("!2^5") == [0]

def test_variables():
	assert ev("a = 5") == [5]
	assert ev("a == 5") == [1]
	assert ev("a^3 - 10^2") == [25]
	assert ev("_") == [25]
	assert ev("b = (_ - 5)^2") == [400]
	assert ev("b") == [400]

def test_builtin_functions():
	assert ev("log10(100)") == [2]
	assert ev("log(e)") == [1]
	assert ev("log(e^4)") == [4]
	assert ev("log2(256)") == [8]
	assert ev("ceil(sqrt(2))") == [2]
	assert ev("round(123.456, 0)") == [123]
	assert ev("round(123456, -3)") == [123000]

def test_misc():
	assert ev("log10(10^3)^3 + 3 * 3^3") == [108]
	assert ev("(( (1-3)^2 - 5) + log2(128) - 1)") == [5]
