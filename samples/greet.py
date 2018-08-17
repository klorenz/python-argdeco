"""
Greeting Module
"""
from argdeco import arg, main

#import rpdb2 ; rpdb2.start_embedded_debugger('foo')

@main( arg("greet", help="the one to greet"), prog='greet' )
def foo(greet):
  print("hello %s" % greet)

if __name__ == "__main__":
    main()
