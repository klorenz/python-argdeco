"""
Create CLI easily.

    >>> from argdeco import arg, CommandDecorator
    >>> command = CommandDecorator(
    ...   arg('')
    ... )
    >>> @command(arg('src', help="a file"), arg('dest', help="dest file"))
    ... def mycommand(src, dest):
    ...    pass
    >>> command.execute(argv)

Or if you want to pass only a single argument

    >>> @command(arg('src', help="a file"), arg('dest', help="dest file"))
    ... def mycommand(args)
    ...    pass
    >>> command.execute(argv, compile=True)

Of if you have a factory for the args:
    >>> @command(arg('src', help="a file"), arg('dest', help="dest file"))
    ... def mycommand(args)
    ...    pass
    >>> command.execute(argv, compile=factory)

"""

import argparse, sys
from textwrap import dedent

class arg:
    """Represent arguments passed with add_argument() to an argparser

    See https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
    """
    def __init__(self, *args, **opts):
        self.args = args
        self.opts = opts

    def apply(self, parser):
        parser.add_argument(*self.args, **self.opts)

class CommandDecorator:
    """
    Create a decorator to decorate functions with their arguments.
    """

    def __init__(self, *args, **kwargs):
        """Initialize CommandDecorator with global arguments

        >>> from argdeco import arg, CommandDecorator
        >>> command = CommandDecorator(
        ...
        ... )

        """
        self.formatter_class = kwargs.get('formatter_class', argparse.RawDescriptionHelpFormatter)

        if 'description' in kwargs:
            self.doc = 'description'
        else:
            self.doc = 'epilog'

        if 'description' not in kwargs and 'epilog' not in kwargs:
            kwargs[self.doc] = sys._getframe().f_back.f_globals.get('__doc__')

        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = self.formatter_class

        # use epilog or description
        #moddoc = sys._getframe().f_back.f_globals.get('__doc__')
        #epilog =

        self.argparser = argparse.ArgumentParser(**kwargs)
        self.commands = None
        #self.commands = self.argparser.add_subparsers()


    def __call__(self, *args, **opts):
        def factory(func):
            _args = args
            if func.__doc__ is not None:
                _doc = dedent(func.__doc__)

                if 'help' not in opts:
                    try:
                        help, desc = _doc.split("\n\n", 1)
                        help = help.strip()

                    except:
                        help = _doc.strip()
                        desc = ''
                else:
                    desc = _doc
            else:
                help = None
                desc = None


            kwargs = {
                'help': help,
                'formatter_class': self.formatter_class,
                self.doc: desc,
            }

            kwargs.update(opts)

            if isinstance(_args[0], basestring):
                if self.commands is None:
                    self.commands = self.argparser.add_subparsers()

                name = _args[0]
                _args = _args[1:]

                command = self.commands.add_parser(name, **kwargs)
            else:
                command = self.argparser

            for a in _args:
                if isinstance(a, arg):
                    a.apply(command)
                else:
                    command.add_argument(a)

            command.set_defaults(action=func)
            return func

        return factory

    def execute(self, argv, compile=None):
        """Parse arguments and execute decorated function

        argv: list of arguments
        compile:
            - None, pass args as keyword args to function
            - True, pass args as single dictionary
            - function, get args from parse_args() and return a pair of
              tuple and dict to be passed as args and kwargs to function
        """
        args = self.argparser.parse_args(argv)
        opts = vars(args).copy()
        del opts['action']

        if compile is None:
            return args.action(**opts)
        elif compile is True:
            return args.action(opts)
        elif compile == 'args':
            return args.action(args)
        else:
            (args, kwargs) = compile(args)
            return args.action(*args, **kwargs)

command_inst = None
def command(*args, **kwargs):
    global command_inst

    if command_inst is None:
        doc = sys._getframe().f_back.f_globals.get('__doc__')
        if doc is not None and 'epilog' not in kwargs and 'description' not in kwargs:
            kwargs['epilog'] = doc
        command_inst = CommandDecorator(**kwargs)
        return command_inst(*args)

    else:
        return command_inst(*args, **kwargs)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    return command_inst.execute(argv)
