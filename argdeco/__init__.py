"""argdeco -- use argparse with decorators

This module is main user interface.  Usually you will use it like this:

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

You can also import:

  - :py:func:`mutually_exclusive`
  - :py:func:`group`
  - :py:func:`config_factory`
  - :py:class:`Config`

"""
from .main import Main
from .command_decorator import CommandDecorator
from .arguments import arg, group, mutually_exclusive, option
from .config import config_factory, Config

opt = option

main    = Main()
command = main.command

__version__ = '2.0.2'
