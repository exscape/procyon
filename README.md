### The Procyon programming language. Written for Python 3 (3.4.2).

Thomas Backman (serenity @ exscape.org)

Note: This project is very new and in its early stages.
The main purpose of this project is for me to learn about how programming languages work.
It is not intended nor likely to ever become useful, considering the wealth of more
mature, faster and overall more compatible programming languages that already exist.

Now, with that said...

#### General features:

* Syntax resembling C, with inspiration from many other languages such as
    Python (chained comparisons e.g. a > b > c, nested functions, hex/oct/bin numbers, etc.),
    Rust (paren-less if statements), Perl (postfix if-statements e.g. "f() if a > b;"), and others.
* REPL with readline support for easy testing and evaluation.
* Uses integer math wherever possible, automatically resorts to float if necessary.
    The result of 6/2 is an int, 3, while the result of 5/2 is a float, 2.5.
    Use the // operator for C-style integer division: 5//2 == 2
* Proper types are still not implemented, however; the above is really the result of Python's type system. Procyon's type system is essentially limited to testing and reporting errors for e.g. subtraction between strings, or addition between numbers and strings.
* Unlimited integer sizes (floats are limited precision, though!)
* Built-in math functions (sqrt, trigonometric functions, abs, round etc.; see .help in the REPL
      for an automatically-updated list)
* if, if/else statements; parenthesis are not required around the test expression, but braces *are* required around the then-body and else-body.
* while loops, along with break and continue statements. Syntax is otherwise the same as for if statements, regarding parenthesis and braces.
* Create functions using the "func" keyword. Nested functions are supported, with proper scoping rules.

Have a look under tests/euler to see some example code that is guaranteed to be up to date (it is automatically tested, so
any time it breaks, I will know).

#### REPL features:

* .vars command to show the value of all variables (except unchanged built-ins, e and pi for now)
* .help command (that is destined to be forever incomplete; listing all language features
      would get old quickly, both for me to write, and for the reader to look through
* .import command to load function definitions from files (the file is interpreted using the current REPL state)
* Value of last evaluation is accessible as _ (in the REPL only)

#### System requirements:

* Python 3 (I have only tested 3.4.2)
* PLY (Python Lex-Yacc)
* Optional: pytest, with plugins pytest-cov and pytest-pep8 (only required for running the tests)
