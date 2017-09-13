# Argument Decorator

I like [argparse] module very much, but if you work with commands with many
subcommands, it is always a bit cumbersome and produces much code in main
methods and you have to separate arguments from the code.  So I started to
write this module.

[argparse]: https://docs.python.org/3/library/argparse.html


## Having only one entry point

Let following program be `greet.py`

```py
"""
Greeting Module
"""
from argdeco import arg, command, main

@command( arg("greet", help="the one to greet"), prog="greet" )
def foo(greet):
  print "hello %s" % greet

if __name__ == "__main__":
  main()

```

Running `python greet.py`:
```
usage: greet [-h] greet
greet: error: too few arguments
```

Running `python greet.py -h`:
```
usage: greet [-h] greet

positional arguments:
  greet       the one to greet

optional arguments:
  -h, --help  show this help message and exit

Greeting Module
```

## Having multiple commands

Let following program be `say.py`

```py
"""
Greeting Module
"""
from argdeco import arg, CommandDecorator, main

# initialize argument parser
command = CommandDecorator(prog="greet")

@command( "hello", arg("greet", help="the one to greet") )
def greet(greet):
  print "hello %s" % greet

@command( "bye", arg("greet", help="the one to say goodbye"))
def geet()

if __name__ == "__main__":
  main()
```
