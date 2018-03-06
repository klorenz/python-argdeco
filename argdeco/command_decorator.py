from argparse import ArgumentParser
from textwrap import dedent
from .arguments import arg
from .config import config_arg

import logging, sys, argparse

logger = logging.getLogger('argdeco.command_decorator')
logger.setLevel(logging.ERROR)

try:
    basestring
except NameError:
    basestring = str

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

        # Arguments

        description:
          Description in argument, also causes that command's function __doc__
          documentation will be also passed as description to add_argument()
          by default.

          If not specified, the calling modules __doc__ will be used as epilogue
          (and all other commands __doc__ will be passed as epilogue).

        formatter_class:
          Default formatter class is argparse.RawDescriptionHelpFormatter.  You
          can override this with passing another formatter_class.

        preprocessor:
          Instead of passing a compile paramter to execute later, you can also
          pass a preprocessor function here.

          Preprocessor function is getting args object as positional argument
          and expanded arguments as kwargs.

          It may return

          # a tuple of (args, kwargs) to be passed to command function
          # a dict, to be passed as kwargs to command function
          # a tuple or list (with not per accident having exact two items
            beeing a tuple and kwargs) passed as positional args to command
            function

        argparser:
          (internal) You may pass an existing argparser instance.

        commands:
          (internal) An object returned from argparser.add_subparsers() method.

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

        if 'preprocessor' in kwargs:
            self.preprocessor = kwargs.pop('preprocessor')
        else:
            self.preprocessor = None

        # use epilog or description
        #moddoc = sys._getframe().f_back.f_globals.get('__doc__')
        #epilog =

        for k in ('commands', 'parent', 'name', 'config_manager'):
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            else:
                setattr(self, k, None)

        if 'argparser' in kwargs:
            self.argparser = kwargs.pop('argparser')
        else:
            self.argparser = ArgumentParser(**kwargs)

        for a in args:
            if isinstance(a, arg):
                a.apply(self.argparser)


    def has_action(self):
        if self.commands is not None:
            return len(self.commands._name_parser_map) > 0
        else:
            return False

    def add_parser(self, command, *args, **kwargs):
        if self.commands is None:
            self.commands = self.argparser.add_subparsers()

        return self.commands.add_parser(command, *args, **kwargs)

    def __getitem__(self, name):
        if self.commands is None:
            raise KeyError(name)

        return self.commands._name_parser_map[name]

    def add_subcommands(self, command, *args, **kwargs):
        """add subcommands.

        If command already defined, pass args and kwargs to add_subparsers()
        method, else to add_parser() method.  This behaviour is for convenience,
        because I mostly use the sequence:

        >>> p = parser.add_parser('foo', help="some help")
        >>> subparser = p.add_subparsers()

        If you want to configure your sub_parsers, you can do it with:

        >>> command.add_subcommands('cmd',
                help = "cmd help"
                subcommands = dict(
                    title = "title"
                    description = "subcommands description"
                )
            )
        """
        subcommands = kwargs.pop('subcommands', None)
        try:
            cmd = self[command]
        except KeyError:
            cmd = self.add_parser(command, *args, **kwargs)
            args, kwargs = tuple(), dict()

        if subcommands is not None:
            kwargs = subcommands

        return CommandDecorator(
            argparser = self.argparser,
            commands  = cmd.add_subparsers(*args, **kwargs),
            parent = self,
            name   = command,
            )

    def update(self, command=None, **kwargs):
        """update data, which is usually passed in ArgumentParser initialization

        e.g. command.update(prog="foo")
        """
        if command is None:
            argparser = self.argparser
        else:
            argparser = self[command]

        for k,v in kwargs.items():
            setattr(argparser, k, v)

    def add_argument(self, *args, **kwargs):
        logger.info("add_argument: %s, %s", args, kwargs)
        if len(args) == 1 and isinstance(args[0], arg):
            args[0].apply(self.argparser)
        else:
            self.argparser.add_argument(*args, **kwargs)

    def add_command(self, command, *args, **kwargs):
        """add a command.

        This is basically a wrapper for add_parser()
        """
        cmd = self.add_parser(command, *args, **kwargs)

    def register_config(self, argument):
        self.config_manager.register(self, argument)

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

            if len(_args) and isinstance(_args[0], basestring):
                name = _args[0]
                _args = _args[1:]

                command = self.add_parser(name, **kwargs)
            else:
                command = self.argparser

            for a in _args:
                if isinstance(a, config_arg):
                    self.register_config(a)

                if isinstance(a, arg):
                    a.apply(command)
                else:
                    command.add_argument(a)

            command.set_defaults(action=func)
            return func

        return factory


    def execute(self, argv=None, compile=None, args_handler=None):
        """Parse arguments and execute decorated function

        argv: list of arguments
        compile:
            - None, pass args as keyword args to function
            - True, pass args as single dictionary
            - function, get args from parse_args() and return a pair of
              tuple and dict to be passed as args and kwargs to function
        """
        if argv is None:
            argv = sys.argv[1:]

        args = self.argparser.parse_args(argv)

        if args_handler:
            result = args_handler(args)
            if result is not None:
                return result

        opts = vars(args).copy()
        del opts['action']

        if compile is None:
            if self.preprocessor:
                compile = self.preprocessor

        if compile is None:
            return args.action(**opts)
        elif compile is True:
            return args.action(opts)
        elif compile == 'args':
            return args.action(args)
        else:
            compiled = compile(args, **opts)

            if isinstance(compiled, dict):
                (_args, _kwargs) = tuple(), compiled
            elif isinstance(compiled, (tuple,list)) and len(compiled) == 2 and isinstance(compiled[1], dict) and isinstance(compiled[0], (tuple,list)):
                (_args, _kwargs) = compiled
            elif isintance(compiled, (tuple,list)):
                (_args, _kwargs) = compiled, dict()
            else:
                raise "Unkown compilation: %s" % compiled

            return args.action(*_args, **_kwargs)

def factory(**kwargs):
    frame = sys._getframe()

    while 'argdeco' in frame.f_globals['__name__']:
        frame = frame.f_back

    doc = frame.f_globals.get('__doc__')
    if doc is not None and 'epilog' not in kwargs and 'description' not in kwargs:
        kwargs['epilog'] = doc
    return CommandDecorator(**kwargs)

command_inst = None
