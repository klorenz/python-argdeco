from argparse import ArgumentParser
from textwrap import dedent
from .arguments import arg

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
            if 'formatter_class' not in kwargs:
                kwargs['formatter_class'] = self.formatter_class

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
            self.add_arguments(*args)
        else:
            self.argparser.add_argument(*args, **kwargs)

    # def register_config_map(self, dest):
    def register_config_map(self, context, dest, config_name):
        if context not in self.config_map:
            self.config_map[context] = {}

        self.config_map[context][dest] = config_name

    #     map_name = self.get_name()
    #     logger.debug("map_name=%s", map_name)
    #     if hasattr(a, 'config_name'):
    #         config_name = a.config_name
    #     else:
    #         config_name = '.'.join([map_name, a.dest])
    #
    #     if map_name not in self.config_map:
    #         self.config_map[map_name] = {}


    def add_arguments(self, *args):
        for a in args:
            a.apply(self.argparser, self, self.get_name())


    def get_config_name(self, action, name):
        '''get the name for configuration

        This returns a name respecting commands and subcommands.  So if you
        have a command name "index" with subcommand "ls", which has option
        "--all", you will pass the action for subcommand "ls"  and the options's
        dest name ("all" in this case), then this function will return
        "index.ls.all" as configuration name for this option.
        '''

        #import rpdb2 ; rpdb2.start_embedded_debugger('foo')

        _name = action.argdeco_name
        config_name = None
        while _name:
            if _name not in self.config_map: continue
            if name in self.config_map[_name]:
                config_name = self.config_map[_name][name]
                break
            _name = _name.rsplit('.', 1)[0]

        assert config_name, "could not determine config name for %s" % k

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

            func.argdeco_name = self.get_name(name)

            self.config_map[func.argdeco_name] = {}

            for a in _args:
                if isinstance(a, arg):
                    a.apply(command, self, context=func.argdeco_name)

                else:
                    command.add_argument(a)

            command.set_defaults(action=func)
            #self.func_map[id(func)] = name
            return func

        return factory

    #def process_args(self, ):



    def execute(self, argv=None, compile=None, preprocessor=None, compiler_factory=None):
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

        # initialize arg processors
        if not preprocessor:
            preprocessor = self.preprocessor

        if not compile:
            compile = self.compile

        if not compiler_factory:
            compiler_factory = self.compiler_factory

        assert not (compiler_factory and compile), \
            "you can either define a compiler factory or a compile function"

        args = self.argparser.parse_args(argv)

        if preprocessor:
            result = preprocessor(args)

            # if preprocessor returns a value, this overrules everything
            # (e.g. print error message and return exit value)
            if result is not None:
                return result

        opts = vars(args).copy()
        del opts['action']

        if compiler_factory:
            compile = compiler_factory(self)

        # if compiler_factory:
        #     def _compile(args, **opts):
        #         cfg = self.compiler_factory(args)
        #
        #         for k,v in opts.items():
        #             _name = args.action.argdeco_name
        #             config_name = None
        #             while _name:
        #                 if _name not in self.config_map: continue
        #                 if k in self.config_map[_name]:
        #                     config_name = self.config_map[_name][k]
        #                     break
        #                 _name = _name.rsplit('.', 1)[0]
        #
        #             assert config_name, "could not determine config name for %s" % k
        #
        #             self.compiler_factory[config_name] = v
        #
        #         return cfg
        #
        #     compile = _compile

        if compile is None or compile == 'kwargs':
            return args.action(**opts)
        elif compile is True or compile == 'dict':
            return args.action(opts)
        elif compile == 'args':
            return args.action(args)
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

            logger.debug("compiled: %s", compiled)

            return args.action(*_args, **_kwargs)

def factory(**kwargs):
    frame = sys._getframe()

    while 'argdeco' in frame.f_globals.get('__name__', ''):
        frame = frame.f_back

    doc = frame.f_globals.get('__doc__')
    if doc is not None and 'epilog' not in kwargs and 'description' not in kwargs:
        kwargs['epilog'] = doc
    return CommandDecorator(**kwargs)

#command_inst = None
