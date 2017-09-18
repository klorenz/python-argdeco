from textwrap import dedent
import subprocess
from os.path import dirname

def run(command):
    cmd = "PYTHONPATH=%s/.. python %s/../samples/%s" % (dirname(__file__), dirname(__file__), command)
    return subprocess.check_output(cmd, shell=True)

def test_argdeco_greet_1():
    assert run("greet.py hello") == dedent("""\
        hello hello
    """)

def test_argdeco_greet_2():
    assert run("greet.py 2>&1 ; exit 0") == dedent("""\
        usage: greet [-h] greet
        greet: error: too few arguments
    """)

def test_argdeco_greet_3():
    assert run("greet.py -h") == dedent("""\
        usage: greet [-h] greet

        positional arguments:
          greet       the one to greet

        optional arguments:
          -h, --help  show this help message and exit

        Greeting Module
    """)

def test_argdeco_parrot_1():
    assert run("parrot.py -h") == dedent("""\
         usage: parrot [-h] {say} ...
         
         positional arguments:
           {say}
             say       let the parrot say something
         
         optional arguments:
           -h, --help  show this help message and exit
         
         Greeting Module
    """)
