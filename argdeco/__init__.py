"""argdeco -- use argparse with decorators

"""
from .main import Main
from .command_decorator import CommandDecorator
from .arguments import arg, group, mutually_exclusive, option
from .config import config_factory, Config

opt = option

main    = Main()
command = main.command
