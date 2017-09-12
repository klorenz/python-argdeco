"""
Greeting Module
"""
import argdeco
from argdeco import arg, command, main

@command( arg("greet", help="the one to greet"), prog='greet' )
def foo(greet):
  print "hello %s" % greet

if __name__ == "__main__":
    main()
