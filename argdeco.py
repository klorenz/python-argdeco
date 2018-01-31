"""
Create CLI easily.

This module provides a decorator factory and a default decorator to easily
decorate functions as commands of a CLI.  This is only a wrapper for the
argparse module.

  arg - wraps add_argument method
  command - is a decorator for functions

  @command('foo', arg('-f', '--file', help="file"), arg('-d', '--debug' help="debug"))
  def foo(file, debug):
      '''help string

      description
      '''

is short for (having ArgumentParser instance argparser):

  p = argparser.add_parser('foo', help="help string", description = "description")
  p.add_argument('-f', '--file', help="file")
  p.add_argument('-d', '--debug', help="debug")
  p.set_defaults(action=foo)

Here a typical sequence

    >>> from argdeco import arg, CommandDecorator

Global arguments here:

    >>> command = CommandDecorator(
    ...   arg('-d', '--debu', action="store_true", help="turn on debug mode")
    ... )

Now you have a decorator for creating subcommands:

>>> @command(arg('src', help="a file"), arg('dest', help="dest file"))
... def mycommand(src, dest):
...    pass

Finally you can execute a decorated function depending on args.

>>> command.execute(sys.argv[1:])

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

import argparse, sys, logging
from textwrap import dedent
from inspect import isfunction

logger = logging.getLogger('argdeco')
logger.setLevel(logging.ERROR)

try:
  basestring
except NameError:
  basestring = str

class ArgAction(argparse.Action):
    def set_arg_func(self, arg_func):
        self.arg_func = arg_func

    def __call__(self, parser, namespace, values, option_string=None):
        if self.arg_func.__code__.co_argcount == 1:
            setattr(namespace, self.dest, self.arg_func(values))
        else:
            self.arg_func(self, parser, namespace, values, option_string)


class arg:
    """Represent arguments passed with add_argument() to an argparser

    See https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
    """
    def __init__(self, *args, **opts):
        self.args = args
        self.opts = opts

    def apply(self, parser):
        logger.info("apply: %s", self)
        parser.add_argument(*self.args, **self.opts)

    def __repr__(self):
        return "arg(%s, %s)" % (self.args, self.opts)

    def __call__(self, *args, **kwargs):
        # factory for other arg
        if not (len(args) == 1 and inspect.isfunction(args[0])):
            _args = self.args
            if len(args):
                _args = args
            _opts = self.opts.copy()
            _opts.update(**kwargs)
            return arg(*_args, **_opts)

        func = args[0]
        self.func = func

        def arg_action_factory(*args, **kwargs):
            a = ArgAction(*args, **kwargs)
            a.set_arg_func(func)
            return a

        self.opts['action'] = arg_action_factory

        return self


class group(arg):
    """Argument group"""

    def apply(self, parser, method='add_argument_group'):
        more_args = self.opts.pop('args', [])
        group = getattr(parser, method)(**self.opts)

        for a in self.args:
            a.apply(group)
        for a in more_args:
            a.apply(group)


class mutually_exclusive(group):
    """Mutually exclusive argument group"""

    def apply(self, parser):
        group.apply(self, parser, 'add_mutually_exclusive_group')


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

        if 'argparser' in kwargs:
            self.argparser = kwargs['argparser']
        else:
            self.argparser = argparse.ArgumentParser(**kwargs)

        if 'commands' in kwargs:
            self.commands = kwargs['commands']
        else:
            self.commands = None

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
            commands  = cmd.add_subparsers(*args, **kwargs)
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

def _init_command_inst(**kwargs):
    #import rpdb2 ; rpdb2.start_embedded_debugger('foo')
    frame = sys._getframe()
    while 'argdeco' in frame.f_globals['__name__']:
        frame = frame.f_back

    doc = frame.f_globals.get('__doc__')
    if doc is not None and 'epilog' not in kwargs and 'description' not in kwargs:
        kwargs['epilog'] = doc
    return CommandDecorator(**kwargs)

#def


command_inst = None
def command(*args, **kwargs):
    """ready to use decorator (without global args)

    >>> from argdeco import command,
    >>> @command()
    ... def ...
    ...
    >>> main()
    """
    global command_inst

    if command_inst is None:
        command_inst = _init_command_inst(**kwargs)
        return command_inst(*args)

    else:
        return command_inst(*args, **kwargs)


class Config:
    pass

class ConfigManager:
    pass



# def main(argv=None):
#     """ready to use main function
#
#     this can be used as main function in case you use the ready to use
#     command decorator
#     """
#     return command_inst.execute(argv)

class Managed:
    pass

class Main:
    def __init__(self,
        debug         = False,
        verbosity     = False,
        quiet         = False,
        compiled      = False,
        command       = None,
        log_format    = "%(name)s %(levelname)s %(message)s",
        error_handler = sys.exit,
        error_code    = 1,
        **kwargs
        ):
        """Initialize main function

        * `debug` - Set True if you want main to manage the debug arg.
          (default: False).
          Set global logging levels to DEBUG and print out full exception stack traces.
        * `verbosity` - control global logging log levels (default: False)
        * `quiet` - set global logging levels to CRITICAL (default: False)
        * `compiled` - pass args in one argument
        * `command` - CommandDecorator instance to use.
        * log_format is log format for logging.basicConfig (default: "%(name)s %(levelname)s %(message)s")
        * `error_code` - code to return on exception (default: 1)
        * `error_handler` - `error_code` will be passed to `error_handler` and
          its result will be returned.  If you pass None, the bare `error_code`
          will be returned (default: `sys.exit`)

        Managed argument means, that the arguments will not be stored in
        arguments list.  You still can access them via the main-function object:

        ```py
        if not main.quiet:
           print("be loud")
        ```
        """
        global command_inst

        # initialize logging
        logging.basicConfig(format=log_format)
        logger = logging.getLogger()
        logger.setLevel(logging.ERROR)

        # initialize error_handler and error_code
        if error_handler is None:
            self.error_handler = lambda x: x
        else:
            self.error_handler = error_handler

        self.error_code = error_code

        # initialize managed argument indicators
        self.arg_debug = debug
        self.arg_quiet = quiet
        self.arg_verbosity = verbosity

        self.debug     = False
        self.verbosity = 0
        self.quiet     = False

        #
        self.compiled_args = compiled

        # initialize command
        if command is None:
            if command_inst is None:
                command_inst = _init_command_inst(**kwargs)

            command = command_inst

        self.command = command

        self.args_compiler = None
        self.main_function = None

    def configure(self, debug=None, quiet=None, verbosity=None):
        """configure managed args
        """
        if debug is not None:
            self.arg_debug = debug
        if quiet is not None:
            self.arg_quiet = quiet
        if verbosity is not None:
            self.arg_verbosity = verbosity

    def init_managed_args(self):
        logger = logging.getLogger()
        _main = self
        if self.arg_debug:
            @arg('--debug', help="print debug output", metavar='', nargs=0)
            def debug_arg(self, parser, namespace, values, option_string=None):
                _main.debug = values
                logger.setLevel(logging.DEBUG)

            self.command.add_argument(debug_arg)

        if self.arg_verbosity:
            @arg('-v', '--verbosity', help="verbosity: set loglevel -v warning, -vv info, -vvv debug", nargs=0, metavar=0)
            def verbosity_arg(self, parser, namespace, values, option_string=None):
                _main.verbosity += 1
                if _main.verbosity == 1:
                    logger.setLevel(logging.WARNING)
                if _main.verbosity == 2:
                    logger.setLevel(logging.INFO)
                if _main.verbosity == 3:
                    logger.setLevel(logging.DEBUG)

            self.command.add_argument(verbosity_arg)

        if self.arg_quiet:
            @arg('--quiet', help="have no output", metavar='', nargs=0)
            def quiet_arg(self, parser, namespace, values, option_string=None):
                logger.setLevel(logging.CRITICAL)
                _main.quiet = True

            self.command.add_argument(quiet_arg)

    def store_args(self, args):
        if self.arg_debug:
            del args.debug
        if self.arg_quiet:
            del args.quiet
        if self.arg_verbosity:
            del args.verbosity

        self.args = args
        if not hasattr(args, 'action'):
            if self.main_function:
                args.action = self.main_function
            else:
                raise RuntimeError("You have to specify an action by either using @command or @main decorator")

    def __call__(self, *args, **kwargs):
        if len(kwargs):
            if kwargs.get('debug'):
                self.arg_debug = kwargs['debug']
                del kwargs['debug']

            if kwargs.get('quiet'):
                self.arg_debug = kwargs['quiet']
                del kwargs['quiet']

            if kwargs.get('verbosity'):
                self.arg_debug = kwargs['verbosity']
                del kwargs['verbosity']

        self.command.update(**kwargs)

        # handle case if called as decorator
        if len(args) == 1 and isfunction(args[0]):
            self.main_function = args[0]
            return args[0]

        argv=None
        for a in args:
            if isinstance(a, arg):
                a.apply(self.command)
            else:
                argv=a

        # at this point we are still in decorating mode
        if argv is None and self.main_function is None and not self.command.has_action():
            return self

        # right before doing the command execution add the managed args
        self.init_managed_args()
        try:
            return self.error_handler(self.command.execute(argv, compile=self.args_compiler, args_handler=self.store_args))

        except StandardError as e:
            if self.debug:
                import traceback
                traceback.print_exc()
            elif not self.quiet:
                sys.stderr.write((u"%s\n" % e).encode('utf-8'))

            return self.error_handler(self.error_code)

main = Main()
