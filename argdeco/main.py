import argdeco.command_decorator as command_decorator
import sys, logging
from inspect import isfunction

from .arguments import arg
from .config import config_arg

PY3 = sys.version_info > (3, 0)

try:
    an_exception = StandardError
except:
    an_exception = Exception

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
            if command_decorator.command_inst is None:
                command_decorator.command_inst = \
                    command_decorator.factory(**kwargs)

            command = command_decorator.command_inst

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
                _main.debug = True
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

    def register_config(self, arg):
        if self.config_manager is None:
            self.command.config_manager = self.config_manager = ConfigManager()
        self.command.register_config(arg)

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
                self.arg_quiet = kwargs['quiet']
                del kwargs['quiet']

            if kwargs.get('verbosity'):
                self.arg_verbosity = kwargs['verbosity']
                del kwargs['verbosity']

        self.command.update(**kwargs)

        # handle case if called as decorator
        if len(args) == 1 and isfunction(args[0]):
            self.main_function = args[0]
            return args[0]

        argv=None
        for a in args:
            if isinstance(a, config_arg):
                self.command.register_config(a)
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

        except an_exception as e:
            logger = logging.getLogger()
            logger.debug("caught exception (self.debug: %s)", self.debug, exc_info=1)

            if self.verbosity:
                import traceback
                traceback.print_exc()
            elif not self.quiet:
                if PY3:
                    sys.stderr.write("%s\n" % e)
                else:
                    sys.stderr.write((u"%s\n" % e).encode('utf-8'))

            return self.error_handler(self.error_code)
