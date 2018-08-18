# Argument Decorator

I like [argparse] module very much, but if you work with commands with many
subcommands, it is always a bit cumbersome and produces much code in main
methods and you have to separate arguments from the code.  So I started to
write this module.

[argparse]: https://docs.python.org/3/library/argparse.html

Here you see only a quick overview, there is also more detailed 
[documentation](https://python-argdeco.readthedocs.io/en/latest/).


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
def bye(name)
  print "bye %s" % name

if __name__ == "__main__":
  main()
```

## The main function

There is a preconfigured `main()` function, which is ready to use.  It 
will manage all commands you have already defined.  When calling the
main function you can also add some global arguments (which actually let
it work without any other command):

```py
"""help text
"""

@main
def my_main_func(foo):
   print(foo)

main(
  arg("--foo", help="pass foo data")
)
```

You have to specify a function to be run from `main()` by either using
command decorators or using the main() decorator.




### Logging and debugging

Main function manages the


## Custom Arguments

You can use `arg()` also as a decorator to write custom actions.  There are two
modes for using this:  Validation Mode, Action Mode

### Validation Mode

This is a simplified variant to be able to do some validations or
transformations of a given value:

```py
import dateutil.parser

from argdeco import arg, command, main

@arg("-d", "--date", help="pass some date")
def arg_date(value):
  # here we can do some validations
  return dateutil.parser.parse(value)

@command("check_date", arg_date)
def check_date(date):
  print(date)

if __name__ == "__main__":
  main()
```


### Action Mode

This is a complex way of as described in the bottom of [action section] in
python docs.

[Custom Action]: https://docs.python.org/2.7/library/argparse.html#action

```py
import dateutil.parser

from argdeco import arg, command, main

@arg("-d", "--date", help="pass some date")
def arg_date(self, parser, namespace, values, option_string=None):
  # here we can do some validations
  setattr(namespace, self.dest, dateutil.parser.parse(values))

@command("check_date", arg_date)
def check_date(date):
  print(date)

if __name__ == "__main__":
  main()
```

The arg_date function is then called from ArgAction's __call__ method with
exactly the same arguments.  `self` argument is current ArgAction instance.


## Development

For publishing run:

   git commit -m "..."
   # change setup.py and change version
   git commit -m "publish v<version>"

   rm dist/*
   python setup.py sdist
   twine upload dist/*

   git tag v<version>
   git push --tags
