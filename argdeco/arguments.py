import logging, inspect
logger = logging.getLogger('argparse.arguments')

from argparse import Action


class ArgAction(Action):
    '''Internal class to handle argument actions

    There are two ways

    '''

    def set_arg_func(self, arg_func):
        self.arg_func = arg_func

    def __call__(self, parser, namespace, values, option_string=None):
        if self.arg_func.__code__.co_argcount == 1:
            setattr(namespace, self.dest, self.arg_func(values))
        else:
            self.arg_func(self, parser, namespace, values, option_string)


class arg(object):
    """Represent arguments passed with add_argument() to an argparser

    See https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
    """
    def __init__(self, *args, **opts):
        if 'config' in opts:
            self.config_name = opts.pop('config')
        if 'config_name' in opts:
            self.config_name = opts.pop('config_name')

        self.args = args
        self.opts = opts

    def apply(self, parser):
        logger.info("apply: %s", self)
        parser.add_argument(*self.args, **self.opts)

    def __getattr__(self, name):
        if name == 'dest':
            dest = self.opts.get('dest')

            if not dest:
                for a in self.args:
                    if a.startswith('--'):
                        dest = a[2:].replace('-', '_')
                        break
                if not dest:
                    for a in self.args:
                        if a.startswith('-'):
                            dest = a[1:].replace('-', '_')
                            break

                if not dest:
                    dest = self.args[0]

            self.dest = dest
            return self.dest

        # if name == 'config_name':
        #     import rpdb2 ; rpdb2.start_embedded_debugger('foo')
        #
        #     path = [self.dest]
        #     cmd = self.command
        #     while cmd:
        #         if cmd.name:
        #             path.append(cmd.name)
        #         cmd = cmd.parent
        #     self.config_name = '.'.join(reversed(path))
        #     return self.config_name

        return object.__getattr__(self, name)

    #     for a in self.args:
    #         if a.startswith('')
    #
    #     cmd =
    #     self.command

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


class option(arg):
    """Option action="store_true" """

    def apply(self, parser):
        logger.info("apply: %s", self)
        opts = self.opts.copy()
        opts['action'] = 'store_true'
        opts['default'] = False

        parser.add_argument(*self.args, **opts)


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
