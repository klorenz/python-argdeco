"""argdeco -- use argparse with decorators

This module is main user interface.

Quickstart
----------

If you want to create a simple program::

    from argdeco import main, arg, opt

    @main(
        arg('--first', help="first argument"),
        opt('--flag-1', help="toggle 1st thing"),
        opt('--flag-2', help="toggle 2nd thing"),
    )
    def my_main(first, flag_1, flag_2):
        # do something here
        pass

    if __name__ == "__main__":
        main()

If you want to create a program with subcommands::

    from argdeco import main, command, arg, opt

    @command('cmd1')
    def cmd1(global_arg):
        print("this is the first command")

    @command("cmd2", arg("--foo-bar"))
    def cmd2(global_arg, foo_bar):
        print("this is the second command with arg: %s" % foo_bar)

    if __name__ == '__main__':
        main(arg('--global-arg', help="a global arg applied to all commands"))

Compiling arguments
-------------------

.. highlight:: py

If you have many arguments it may get cumbersome to list all the arguments in
the decorator and the function::

    @command('cmd1',
        arg('--first', '-f'),
        arg('--second', '-s'),
        arg('--third', '-t'),
        arg('--fourth', '-F'),
    )
    def cmd1(first, second, third, fourth):
        pass

Think of having many of such functions maybe even repeating some arguments.
Then it becomes handy to use compiled arguments::

    from argdeco import main, command

    @command('cmd',
        arg('--first', '-f'),
        arg('--second', '-s'),
        arg('--third', '-t'),
        arg('--fourth', '-F'),
    )
    def cmd1(opts):
        if opts['first'] == '1':
            ...

    if __name__ == '__main__':
        main(compile=True)

``compile`` can have following values:

===========  ===========  =====================================================
  Value        Alias       Description
===========  ===========  =====================================================
  None        'kwargs'    Passed to handler as keyword arguments
  True        'dict'      Args passed to handler as single dictionary
  'args'                  Pass args namespace as returned from :py:meth:`argparse.ArgumentParser.parse_args`
  function                You can also pass a function, which is explained in `Compile functions`_
===========  ===========  =====================================================

Compile to args::

    from argdeco import main, command

    @command('cmd',
        arg('--first', '-f'),
        arg('--second', '-s'),
        arg('--third', '-t'),
        arg('--fourth', '-F'),
    )
    def cmd1(args):
        if args.first == '1':
            ...

    if __name__ == '__main__':
        main(compile='args')


Compile functions
'''''''''''''''''

If you need even more control of your arguments, you can pass custom compile
functions, which gets args namespace and opts keyword arguments as parameter
and is expected to return:

================  =================================================================
   type           description
================  =================================================================
   dict           This will be passed as keyword arguments to handler function
   tuple/list     A tuple with two values, a list (or tuple) and a dictionary,
                  which are passed as args and kwargs to handler.
   list/tuple     If the tuple or list does not match requirements in above,
                  it is assumed, that no kwargs shall be passe and this is the
                  args list for positional parameters.
================  =================================================================

You can use such a function work preprocessing some args and manipulate the
parameters passed to the handlers.




Compiler factory
''''''''''''''''

Compile functions are usually not directly connected with command decorator and
usually do not know about it (unless you share it globally).  If you need to
access data from command decorator instance or need for other reasons more
control of argument setup, you can use a compiler factory.

A compiler factory is initialized with :py:class:`CommandDecorator` instance.

It must return a function, which will get args as returned from
:py:meth:`argparse.ArgumentParser.parse_args` and keyword arguments.

Here you see the most simplest one::

    def my_factory(command):
        def my_compiler(args, **opts):
            return opts

        return my_compiler


Validating and transforming arguments
-------------------------------------

With :py:class:`argparse.Action` :py:mod:`argparse` module provides a method
to provide custom argument handlers.  :py:mod:`argdeco` provides some eases
for this as well::

    from argdeco import arg, command, main
    import dateutil.parser

    @arg('--date', '-d')
    def arg_date(value):
        return dateutil.parser.parse(value)

    @main(arg_date)
    def handle_date(date)
        print(date.isoformat())

    main()


There is also a complex (more powerful) way, which is ::

    import dateutil.parser

    from argdeco import arg, command, main

    @arg("-d", "--date", help="pass some date")
    def arg_date(self, parser, namespace, values, option_string=None):
         # here we can do some validations
         print "self: %s" % self
         setattr(namespace, self.dest, dateutil.parser.parse(values))

    @command("check_date", arg_date)
    def check_date(date):
        print(date)

    main()


Working with subcommands
------------------------

You may want to implement a CLI like git has.  This is quite easy with
:py:mod:`argdeco`::

    from argdeco import main, command, arg, opt
    from textwrap import dedent

    # we will implement a sample `remote` command here

    # global arguments (for all commands)
    main(
        arg('--config-file', '-C', help="pass a config file"),
    )

    # create a new decorator for sub-command 'remote' actions
    remote_command = command.add_subcommands('remote',
        help="manage remote sites",  # description in global command list
        subcommands = dict(
            title = "remote commands",   # caption of subcommand list
            description = dedent('''\
                Here is some documentation about remote commands.

                There is a lot to say ...
            ''')
        )
    )

    @remote_command('add',
        arg('remote_name', help="name of remote site"),
        arg('url', help="url of remote site"),
        opt('--tags', help="get all tags when requesting remote site"),
    )
    def cmd_remote_add(config_file, remote_name, url, tags):
        ...

    @remote_command('rename',
        arg('old_name', help="old name of remote"),
        arg('new_name', help="new name of remote"),
    )
    def cmd_remote_rename(config_file, old_name, new_name):
        ...

If you run ``add_subcommands(..., subcommands={...})``, all the
keyword arguments of add_subcommands, except the ``subcommands`` one, will be passed
to :py:meth:`argparse.ArgumentParser.add_parser` and the subcommands dictionary
will be passed as keyword arguments to
:py:meth:`argparse.ArgumentParser.add_subparsers`.

"""
from .main import Main
from .command_decorator import CommandDecorator
from .arguments import arg, group, mutually_exclusive, opt
from .config import config_factory, ConfigDict

PYTHON_ARGCOMPLETE_OK = True

option = opt

main    = Main()
command = main.command

__version__ = '2.1.6'

#
