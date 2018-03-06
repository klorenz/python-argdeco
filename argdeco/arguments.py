import logging, inspect
logger = logging.getLogger('argparse.arguments')

from argparse import Action


class ArgAction(Action):

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
