from textwrap import dedent
import subprocess
from os.path import dirname

import sys
if (sys.version_info > (3, 0)):
    PY3 = True
else:
    PY3 = False


def run(command):
    cmd = "python %s/../samples/%s" % (dirname(__file__), command)
    return subprocess.check_output(cmd, shell=True, env={'PYTHONPATH': "%s/.." % dirname(__file__)}).decode('utf-8')

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

def test_argdeco_parrot_2():
    assert run("parrot.py say --help") == dedent("""\
          usage: parrot say [-h] {hello,bye} ...

          description of say command

          positional arguments:
            {hello,bye}
              hello      this line is command help
              bye        some help instead of first line of docstring
          
          optional arguments:
            -h, --help   show this help message and exit
    """)

def test_argdeco_parrot_3():
    assert run("parrot.py say hello --help") == dedent("""\
          usage: parrot say hello [-h] greet
          
          positional arguments:
            greet       the one to greet

          optional arguments:
            -h, --help  show this help message and exit

          And this will be in epilog. 

          Here some details.
    """)