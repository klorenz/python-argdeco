""" argdeco.main -- the main function

This module provides :py:class:`~argdeco.main.Main`, which can be used to create main
functions.

For ease it provides common arguments like `debug`, `verbosity` and `quiet`
which control whether you want to print stacktraces, and how verbose the logging
is.  These arguments will not be passed to command handlers or main function
handler.

Usually you will import the global main instance provided in argdeco::

    from argdeco import main

In this case, `main.command` is also provided as global symbol::

    from argdeco import main, command

    @main.command(...)
    def cmd(...):
        ...

    # is equivalent to
    @command(...)
    def cmd(...):
        ...

Bug you can also create an own instance::

   from argdeco.main import Main
   main = Main()

   @main.command('foo', ...)
   def my_cmd(...):
       ...

If you want to make use of the predefined (global) args::

   if __name__ == '__main__':
       main(verbosity=True, debug=True, quiet=True)

"""

import argdeco.command_decorator as command_decorator
import sys, logging
from inspect import isfunction
import argparse

import os
from os.path import expanduser

from .arguments import arg

PY3 = sys.version_info > (3, 0)

try:
    an_exception = StandardError
except:
    an_exception = Exception

class ArgParseExit(an_exception):
    def __init__(self, error_code, message):
        self.error_code=error_code
        self.message = message

    def __str__(self):
        if self.message:
            return self.message.strip()
        else:
            return ''


class Main:
    """Main function provider

    An instance of this class can be used as main function for your program.
    It provides a :py:attribute:


    :param debug: Set True if you want main to manage the debug arg.
        (default: False).

        Set global logging levels to DEBUG and print out full exception
        stack traces.

    :param verbosity:
        Control global logging log levels (default: False)

        If this is turned on, default log level will be set to ``ERROR`` and
        following argument are provided:

        .. option:: -v, --verbose

           set log level to level ``WARNING``

        .. option:: -vv, -v -v, --verbose --verbose

           Set log level to level ``INFO``

        .. option:: -vvv, -v -v -v

           Set log level to level ``DEBUG``

    :param quiet:
        If you set this to ``True``, argument :option:`--quiet` will be
        added:

        .. option:: --quiet

           If this option is passed, global log level will be set to
           ``CRITICAL``.

    :param command:
        CommandDecorator instance to use.  This defaults to None, and for
        each main instance there will be created a
        :py:class:`~argdeco.command_decorator.CommandDecorator`
        instance.

    :param compile:
        This parameter is passed
        :py:class:`~argdeco.command_decorator.CommandDecorator`
        instance and controls, if arguments passed to handlers are compiled in
        some way.

    :param compiler_factory:
        This parameter is passed
        :py:class:`~argdeco.command_decorator.CommandDecorator`
        instance and defines a factory function, which returns a compile
        function.

        You may either use ``compile`` or ``compiler_factory``.

    :param log_format:
        This parameter is passed to :py:func:`logging.basicConfig` to
        define log output.  (default: ``"%(name)s %(levelname)s %(message)s"``)

    :param error_code:
        This is the error code to be returned on an exception (default: 1).

    :param error_handler:
        Pass a function, which handles errors.  This function will get the
        error code returned from a command (or main) function and do
        something with it.  Default is :py:func:`sys.exit`.

        If you do not want to exit the program after running the main
        funtion you have to set ``error_handler`` to ``None``.

    If you want to access the managed arguments (quiet, verbosity, debug),
    you can access them as attributes of the main instance::

        if not main.quiet:
            print("be loud")

        if main.debug:
            print("debug is on")
    """

    def __init__(self,
        debug         = False,
        verbosity     = False,
        quiet         = False,
        compile       = None,
        compiler_factory = None,
        command       = None,
        log_format    = "%(name)-20.20s %(levelname)-10.10s %(message)s",
        error_handler = sys.exit,
        error_code    = 1,
        **kwargs
        ):

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


    def configure(self, debug=None, quiet=None, verbosity=None, compile=None, compiler_factory=None, **kwargs):
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

        if kwargs:
            # other keyword arguments update command attribute
            self.command.update(**kwargs)

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

    def uninstall_bash_completion(self, script_name=None, dest="~/.bashrc"):
        '''remove line to activate bash_completion for given script_name from given dest

        You can use this for letting the user uninstall bash_completion::

            from argdeco import command, main

            @command("uninstall-bash-completion",
                arg('--dest', help="destination", default="~/.bashrc")
            )
            def uninstall_bash_completion(dest):
                main.uninstall_bash_completion(dest=dest)
        '''
        if 'USERPROFILE' in os.environ and 'HOME' not in os.environ:
            os.environ['HOME'] = os.environ['USERPROFILE']
        dest = expanduser(dest)
        if script_name is None:
            script_name = sys.argv[0]
        lines = []
        remove_line = 'register-python-argcomplete %s' % script_name
        with open(dest, 'r') as f:
            for line in f:
                if line.strip().startswith('#'):
                    lines.append(line)
                    continue

                if remove_line in line: continue
                lines.append(line)
        with open(dest, 'w') as f:
            f.write(''.join(lines))

    def install_bash_completion(self, script_name=None, dest="~/.bashrc"):
        '''add line to activate bash_completion for given script_name into dest

        You can use this for letting the user install bash_completion::

            from argdeco import command, main

            @command("install-bash-completion",
                arg('--dest', help="destination", default="~/.bashrc")
            )
            def install_bash_completion(dest):
                main.install_bash_completion(dest=dest)

        '''
        if 'USERPROFILE' in os.environ and 'HOME' not in os.environ:
            os.environ['HOME'] = os.environ['USERPROFILE']
        dest = expanduser(dest)
        if script_name is None:
            script_name = sys.argv[0]

        self.uninstall_bash_completion(script_name=script_name, dest=dest)
        with open(dest, 'a') as f:
            f.write('eval "$(register-python-argcomplete %s)"\n' % script_name)

    def add_arguments(self, *args):
        """Explicitely add arguments::

            main.add_arguments( arg('--first'), arg('--second') )

        This function wraps :py:meth:`argdeco.command_decorator.C`

        :param \*args:
            arguments to be added.
        """
        self.command.add_arguments(*args)

    def __call__(self, *args, **kwargs):
        """
        You can call :py:class:`~argdeco.main.Main` instance in various ways.  As function or
        as decorator.   As long you did not have decorated a function with this
        :py:class:`~argdeco.main.Main` instance, you can invoke it as function for confiugration.

        As soon there is defined some action, invoking the instance, will execute
        the actions.

        Configure some global arguments::

            main(
                arg('--global', '-g', help="a global argument"),
            )

        Decorate a function to be called as main function::

            @main
            def my_main():
                return 0

            if __name__ == "__main__":
                main()

        Decorate a function to be main function and define arguments of it::

            @main(
                arg('--first', '-f', help="first argument"),
                arg('--second', '-s', help="second argument"),
            )
            def main(first, second):
                return 0   # successful

            if __name__ == "__main__":
                main(debug=True)

        :param \*args:
            All arguments of type :py:class:`~argdeco.command_decorator.arg` are filtered out and added
            as global argument to underlying
            :py:class:`~argdeco.command_decorator.CommandDecorator` instance.

            All other arguments are collected -- if any to be `argv`.  If
            there are any other parameters, this function switches into regular
            `main` mode and will execute the main function passing `argv`.  If
            there are no arguments defined, :py:attr:`sys.argv` is used as
            default.

        :param \*\*kwargs:
            You can pass various keyword arguments to tweak behaviour of the
            main function.

            :argv:
                You can set explicitly the ``argv`` vector.  This becomes handy,
                if you want to pass an empty ``argv`` list and do not want to
                use the default sys.argv.

            :debug:
                Turn on debug argument, see :py:class:`~argdeco.main.Main` for more info.

            :verbosity:
                Turn on verbose argument, see :py:class:`~argdeco.main.Main` for more info.

            :quiet:
                Turn on quiet argument, see :py:class:`~argdeco.main.Main` for more info.

            :error_handler:
                Tweak the error handler.  This will be only local to this call.

            :compile:
                Set compile for this call.

            :compiler_factory:
                Set compiler_factory for this call.

        :return:
            :Decorator mode:
                Returns the instance itself, to be invoked as decorator.
            :Run mode:
                Returns whatever error_handler returns, when getting the return
                value of the invoked action function
        """

        error_handler    = self.error_handler
        compile          = self.compile
        compiler_factory = self.compiler_factory

        _locals = locals()

        # filter out all keyword arguments, which are handled by this class
        for k in [k for k in kwargs.keys()]:
            # handle args arg_debug, arg_quiet, etc.
            if hasattr(self, 'arg_'+k):
                setattr(self, 'arg_'+k, kwargs.pop(k))
            elif hasattr(self, k):
                if k in _locals:
                    _locals[k] = kwargs.pop(k)

        argv=None
        if 'argv' in kwargs:
            argv = kwargs.pop('argv')

        # other keyword arguments update command attribute
        self.command.update(**kwargs)

        # set a custom exit function
        def _exit(result=0, message=None):
            raise ArgParseExit(result, message)
            #return error_handler(result)
        self.command.update(exit=_exit)

        # handle case if called as decorator
        if len(args) == 1 and isfunction(args[0]):
            self.main_function = args[0]
            return args[0]

        # filter out argument definitions from posional arguments and create
        # argv list, if any
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

        if argv is not None and self.main_function is None and not self.command.has_action():
            raise ValueError("Main cannot handle any arguments, when main_function is not yet defined")

        # at this point we are still in decorating mode
        if argv is None and self.main_function is None and not self.command.has_action():
            return self

        self.exception = None

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

            self.exception = e
            if hasattr(e, 'error_code'):
                return error_handler(e.error_code)
            else:
                return error_handler(self.error_code)
