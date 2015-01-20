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
    Rust (paren-less if statements), and others.
* REPL with readline support for easy testing and evaluation.
* Uses integer math wherever possible, automatically resorts to float if necessary.
    The result of 6/2 is an int, 3, while the result of 5/2 is a float, 2.5.
    Use trunc(5/2) for C-style integer division.
* Unlimited integer sizes (floats are limited precision, though!)
* Built-in math functions (sqrt, trigonometric functions, abs, round etc.; see .help in the REPL
      for an automatically-updated list)

#### REPL features:

* .vars command to show the value of all variables (except unchanged built-ins, e and pi for now)
* .help command (that is destined to be forever incomplete; listing all language features
      would get old quickly, both for me to write, and for the reader to look through
* Value of last evaluation is accessible as _ (actually, this is true in the language itself)
