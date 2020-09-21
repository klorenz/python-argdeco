from argparse import ArgumentParser
from textwrap import dedent
from .arguments import arg
import os

import logging, sys, argparse

logger = logging.getLogger('argdeco.command_decorator')

try:
    basestring
except NameError:
    basestring = str

class Undefined:
    pass

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

        compiler_factory:
          Passing a compiler_factory is another way of providing a argument
          compiler.

          `compiler_factory` is expected to be a function getting one parameter
          -- the args as returned from `argparser.parseargs()``.  It is espected
          to return a dictionary like object.  For each given argument the
          name of the argument is computed and the corresponding configuration
          item is set.

          Example:

              >>> command = CommandDecorator(compiler_factory=lambda x: {})
              >>> @command('foo', arg('--bar'))
              >>> def cmd(cfg):
              ...     assert cfg['foo.bar'] == '1'
              >>> command.execute(['foo', '--bar', '1'])

        """
        self.formatter_class = kwargs.get('formatter_class', argparse.RawDescriptionHelpFormatter)

        if 'description' in kwargs:
            self.doc = 'description'
        else:
            self.doc = 'epilog'

        if 'description' not in kwargs and 'epilog' not in kwargs:
            kwargs[self.doc] = sys._getframe().f_back.f_globals.get('__doc__')
            if kwargs[self.doc] is not None:
                kwargs[self.doc] = dedent(kwargs[self.doc])

        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = self.formatter_class

        if 'preprocessor' in kwargs:
            self.preprocessor = kwargs.pop('preprocessor')
        else:
            self.preprocessor = None

        # use epilog or description
        #moddoc = sys._getframe().f_back.f_globals.get('__doc__')
        #epilog =

        for k in ('commands', 'parent', 'name', 'compiler_factory'):
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            else:
                setattr(self, k, None)

        self.config_map = {}
        self.compile = None

        if 'argparser' in kwargs:
            self.argparser = kwargs.pop('argparser')
        else:
            self.argparser = ArgumentParser(**kwargs)

        for a in args:
            if isinstance(a, arg):
                a.apply(self.argparser, self, self.get_name())

        self.children = []


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

        cmd = self
        items = name.split('.')
        path, name = items[:-1], items[-1]

        for k in path:
            _map = dict((c.name, c) for c in cmd.children)
            if k not in _map:
                raise KeyError(name)
            cmd = _map[k]

        return cmd.commands._name_parser_map[name]

    def get_action(self, name):
        return self[name].get_default('action')

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
            if 'formatter_class' not in kwargs:
                kwargs['formatter_class'] = self.formatter_class

            cmd = self.add_parser(command, *args, **kwargs)
            args, kwargs = tuple(), dict()

        if subcommands is not None:
            kwargs = subcommands

        child = CommandDecorator(
            argparser = self.argparser,
            commands  = cmd.add_subparsers(*args, **kwargs),
            parent = self,
            name   = command,
            )
        self.children.append(child)

        return child

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
        logger.debug("add_argument: %s, %s", args, kwargs)
        if len(args) == 1 and isinstance(args[0], arg):
            self.add_arguments(*args)
        else:
            self.argparser.add_argument(*args, **kwargs)

    # def register_config_map(self, dest):
    def register_config_map(self, context, dest, config_name):
        logger.debug("register_config_map: context=%s, dest=%s, config_name=%s", context, dest, config_name)

        _root = self
        while _root.parent is not None:
            _root = _root.parent

        if context not in _root.config_map:
            _root.config_map[context] = {}

        _root.config_map[context][dest] = config_name

    #     map_name = self.get_name()
    #     logger.debug("map_name=%s", map_name)
    #     if hasattr(a, 'config_name'):
    #         config_name = a.config_name
    #     else:
    #         config_name = '.'.join([map_name, a.dest])
    #
    #     if map_name not in self.config_map:
    #         self.config_map[map_name] = {}


    def add_arguments(self, *args, **kwargs):
        context = kwargs.get('context')
        argparser = kwargs.get('argparser')
        if context is None:
            context = self.get_name()

        if argparser is None:
            argparser = self.argparser

        for a in args:
            if isinstance(a, basestring):
                a = arg(a)
            elif isinstance(a, dict):
                a = arg(**a)
            elif isinstance(a, (tuple,list)):
                a = arg(*a)
            elif not isinstance(a, arg):
                raise ValueError("cannot convert %s into arg type" % a)

            a.apply(argparser, self, context=context)


    def get_config_name(self, action, name=None):
        '''get the name for configuration

        This returns a name respecting commands and subcommands.  So if you
        have a command name "index" with subcommand "ls", which has option
        "--all", you will pass the action for subcommand "ls"  and the options's
        dest name ("all" in this case), then this function will return
        "index.ls.all" as configuration name for this option.
        '''

        _name = None

        if name is None:
            if '.' in action:
                action, name = action.rsplit('.', 1)
            else:
                _name = ''
                name = action

        if _name is None:
            if isinstance(action, basestring):
                action = self.get_action(action)
            _name = action.argdeco_name

        logger.debug("_name=%s", _name)

        config_name = Undefined
        while True:
            logger.debug("check _name=%s, name=%s", repr(_name), repr(name))

            if _name in self.config_map:
                if name in self.config_map[_name]:
                    config_name = self.config_map[_name][name]
                    if config_name is not None:
                        if config_name.startswith('.'):
                            config_name = _name + config_name
                    break

            if _name == '':
                break

            if '.' not in _name:
                _name = ''
                continue

            _name = _name.rsplit('.', 1)[0]

        assert config_name is not Undefined, "could not determine config name for %s" % name
#        if config_name.startswith('.'):
#            config_name = config_name[1:]
        return config_name


    def add_command(self, command, *args, **kwargs):
        """add a command.

        This is basically a wrapper for add_parser()
        """
        cmd = self.add_parser(command, *args, **kwargs)


    def get_name(self, name=None):
        if name is not None:
            path = [name]
        else:
            path = []

        cmd = self
        while cmd:
            if cmd.name:
                path.append(cmd.name)
            cmd = cmd.parent

        return '.'.join(reversed(path))

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
                name = None
                command = self.argparser

            func.argdeco_name = context = self.get_name(name)
            self.config_map[func.argdeco_name] = {}

            self.add_arguments(*_args, argparser=command, context=context)

            command.set_defaults(action=func)

            return func

        return factory

    def compile_args(self, argv=None, compile=None, preprocessor=None,
        compiler_factory=None):

        logger.debug(
            "argv=%s, compile=%s, preprocessor=%s, compiler_factory=%s",
            argv, compile, preprocessor, compiler_factory)

        if argv is None:
            argv = sys.argv[1:]

        # initialize arg processors
        if not preprocessor:
            preprocessor = self.preprocessor

        if not compile:
            compile = self.compile

        if not compiler_factory:
            compiler_factory = self.compiler_factory

        assert not (compiler_factory and compile), \
            "you can either define a compiler factory or a compile function"

#        if 'BASH' in os.environ:
#            if '_python_argcomplete_run' not in os.environ:
#                logger.warning("Autocomplete is not activated.  See https://github.com/kislyuk/argcomplete#activating-global-completion for activating")
        if compiler_factory:
            compile = compiler_factory(self)

        import argcomplete
        argcomplete.autocomplete(self.argparser)
        args = self.argparser.parse_args(argv)

        if preprocessor:
            result = preprocessor(args)

            # if preprocessor returns a value, this overrules everything
            # (e.g. print error message and return exit value)
            if result is not None:
                return result

        opts = vars(args).copy()
        del opts['action']

        if compile is None or compile == 'kwargs':
            (_args, _kwargs) = tuple(), opts
        elif compile is True or compile == 'dict':
            (_args, _kwargs) = (opts,), dict()
        elif compile == 'args':
            (_args, _kwargs) = (args,), dict()
        else:
            compiled = compile(args, **opts)

            if isinstance(compiled, dict):
                (_args, _kwargs) = tuple(), compiled
            elif isinstance(compiled, (tuple,list)) and len(compiled) == 2 and isinstance(compiled[1], dict) and isinstance(compiled[0], (tuple,list)):
                (_args, _kwargs) = compiled
            elif isinstance(compiled, (tuple,list)):
                (_args, _kwargs) = compiled, dict()
            else:
                raise "Unkown compilation: %s" % compiled

        #logger.debug("compiled: %s", (_args, _kwargs))
        return (args.action, _args, _kwargs)


    def execute(self, argv=None, compile=None, preprocessor=None, compiler_factory=None):
        """Parse arguments and execute decorated function

        argv: list of arguments
        compile:
            - None, pass args as keyword args to function
            - True, pass args as single dictionary
            - function, get args from parse_args() and return a pair of
              tuple and dict to be passed as args and kwargs to function
        """

        action, args, kwargs = self.compile_args(argv=argv, compile=compile, preprocessor=preprocessor, compiler_factory=compiler_factory)
        return action(*args, **kwargs)


def factory(**kwargs):
    frame = sys._getframe()

    while 'argdeco' in frame.f_globals.get('__name__', ''):
        frame = frame.f_back

    doc = frame.f_globals.get('__doc__')
    if doc is not None and 'epilog' not in kwargs and 'description' not in kwargs:
        kwargs['epilog'] = doc
    return CommandDecorator(**kwargs)

#command_inst = None
