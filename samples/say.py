#!/usr/bin/env python
"""
Greeting Module
"""
from argdeco import arg, CommandDecorator, main

# initialize argument parser
command = CommandDecorator(prog="greet")

@command( "hello", arg("greet", help="the one to greet") )
def greet(greet):
    """
    this line is command help

    And this will be in epilog. here some details.
    """
    print("hello %s" % greet)

@command( "bye",
    arg("greet", help="the one to say goodbye"),
    help="some help instead of first line of docstring")
def bye(bye):
    print("goodbye %s" % bye)

if __name__ == "__main__":
    command.execute()
