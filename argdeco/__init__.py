
from .main import Main
from .command_decorator import CommandDecorator
from .arguments import arg, group, mutually_exclusive, option
opt = option

main    = Main()
command = main.command
