import argdeco.command_decorator as command_decorator
import sys, logging
from inspect import isfunction
import argparse

from .arguments import arg

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
        compile       = None,
        compiler_factory = None,
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
        * `compile` - pass args in one argument
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
        #self.compiled_args = compiled

        # initialize command
        if command is None:
            command = command_decorator.factory(**kwargs)
            #if command_decorator.command_inst is None:
                #command_decorator.command_inst = \
                    #command_decorator.factory(**kwargs)
#
            #command = command_decorator.command_inst

        self.command = command

        self.compile = compile
        self.compiler_factory = compiler_factory
        self.main_function = None

    def configure(self, debug=None, quiet=None, verbosity=None, compile=None, compiler_factory=None):
        """configure managed args
        """
        if debug is not None:
            self.arg_debug = debug
        if quiet is not None:
            self.arg_quiet = quiet
        if verbosity is not None:
            self.arg_verbosity = verbosity
        if compile is not None:
            self.compile = compile
        if compiler_factory is not None:
            self.compiler_factory = compiler_factory

    def init_managed_args(self):
        logger = logging.getLogger()

        _main = self
        _main.verbosity = 0
        if self.arg_debug:
            @arg('--debug', help="print debug output", metavar='', nargs=0)
            def debug_arg(self, parser, namespace, values, option_string=None):
                _main.debug = True
                logger.setLevel(logging.DEBUG)

            try:
                self.command.add_argument(debug_arg)
            except argparse.ArgumentError:
                pass

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

            try:
                self.command.add_argument(verbosity_arg)
            except argparse.ArgumentError:
                pass

        if self.arg_quiet:
            @arg('--quiet', help="have no output", metavar='', nargs=0)
            def quiet_arg(self, parser, namespace, values, option_string=None):
                logger.setLevel(logging.CRITICAL)
                _main.quiet = True

            try:
                self.command.add_argument(quiet_arg)
            except argparse.ArgumentError:
                pass

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

    def add_arguments(self, *args):
        self.command.add_arguments(*args)

    def __call__(self, *args, **kwargs):
        error_handler    = self.error_handler
        compile          = self.compile
        compiler_factory = self.compiler_factory

        _locals = locals()

        # filter out all keyword arguments, which are handled by this class
        for k in kwargs.keys():
            # handle args arg_debug, arg_quiet, etc.
            if hasattr(self, 'arg_'+k):
                setattr(self, 'arg_'+k, kwargs.pop(k))
            elif hasattr(self, k):
                if k in _locals:
                    _locals[k] = kwargs.pop(k)

        # other keyword arguments update command attribute
        self.command.update(**kwargs)

        # set a custom exit function
        def _exit(result=0, message=None):
            if message:
                if not message.endswith("\n"):
                    print(message)
                else:
                    sys.stdout.write(message)
            return error_handler(result)
        self.command.update(exit=_exit)

        # handle case if called as decorator
        if len(args) == 1 and isfunction(args[0]):
            self.main_function = args[0]
            return args[0]

        # filter out argument definitions from posional arguments and create
        # argv list, if any
        argv=None
        for a in args:
            if isinstance(a, arg):
                self.command.add_argument(a)
            else:
                if argv is None:
                    argv = []
                argv.append(a)

        # if there were no argv args and there is not yet defined a main,
        # function defined and there are no commands defined yet.  Return
        # this object, that there may be defined a function in a subsequent
        # call (this is the case if @main(args...) is used).

        # at this point we are still in decorating mode
        if argv is None and self.main_function is None and not self.command.has_action():
            return self

        # right before doing the command execution add the managed args
        self.init_managed_args()
        try:
            return error_handler(self.command.execute(argv, compile=compile, preprocessor=self.store_args, compiler_factory=compiler_factory))

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

            return error_handler(self.error_code)
