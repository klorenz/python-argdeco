.. argdeco documentation master file, created by
   sphinx-quickstart on Fri Aug 17 10:11:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. highlight:: py

argdeco -- Command line interfaces with decorators
==================================================

I like :py:mod:`argparse` module very much, because you can create great
and sophisticating command line argument configurations.  But if you create
many small tools or if you even work with subcommands, it gets a bit
cumbersome and you produce a lot of code, which destracts from essentials.

This module aims to ease creating of command line interfaces using the power
of decorators wrapping :py:mod:`argparse`.


Install
-------

Install it using pip::

    pip install argdeco


Overview
--------

Example for a simple main::

  from argdeco import main, arg, opt

  @main(
      arg('--input', '-i', help="input file", default="-"),
      arg('--output', '-o', help="output file", default="-"),
      opt('--flag'),
  )
  def main(input, output, flag):
      input  = (input  == '-') and sys.stdin  or open(input,  'r')
      output = (output == '-') and sys.stdout or open(output, 'w')

      if flag:
         print("flagged")

      for line in input:
          output.write(line)

  if __name__ == '__main__':
      main()

You can run the command with:

.. code-block:: shell

   $ echo "x" | copy.py --flag
   flagged
   x

Example for commands::

  from argdeco import main, command, arg

  @command( "hello", arg("greet", help="the one to greet") )
  def greet(greet):
      """
      greet a person.

      This command will print out a greeting to the person
      named in the argument.
      """
      print("hello %s" % greet)

  @command( "bye", arg("greet", help="the one to say goodbye") )
  def bye(greet):
      """
      say goodbye to a person.

      This command will print out a goodbye to the person
      named in the argument.
      """
      print("goodbye %s" % greet)

  if __name__ == "__main__":
      main()

Here some run examples:

.. code-block:: shell

   $ greet.py hello "Mr. Bean"
   hello Mr. Bean

   $ greet.py bye "Mr. Bean"
   goodby Mr. Bean

You might have noticed, that arguments passed to :py:class:`arg` are the same
like the ones passed to :py:meth:`argparse.ArgumentParser.add_argument`.

Bash completion
---------------

argdeco uses `argcomplete`_ by default.


Enable completion for your script
'''''''''''''''''''''''''''''''''

If you install your script as ``myscript`` executable, you have to make sure,
that following line is in the user's ``~/.bashrc``::

    eval "$(register-python-argcomplete myscript)"


Global completion activation
''''''''''''''''''''''''''''

For activating it globally, a user has to `activate global completion`_.

.. note::

    On a Ubuntu system, you can it install as a user with::

       activate-global-python-argcomplete --user

    This installs the completion script to ``~/.bash_completion.d/``.  This
    is not automatically invoked.

    So create a ``~/.bash_completion`` file to enable ``~/.bash_completion.d/``::

        echo "for f in ~/.bash_completion/* ; do source $f ; done" > ~/.bash_completion

In your script you have to make sure, that the string PYTHON_ARGCOMPLETE_OK can
be found within the first 1024 characters in your executable.

If you use a custom python script (installed via setup scripts) as entry
point, you can achieve this by importing a symbol for activating completion::

   from argdeco import main, command, arg, PYTHON_ARGCOMPLETE_OK

If you specify an entry point in your setup.py, you should call the entrypoint
PYTHON_ARGCOMPLETE_OK::

    setup(
       # ...
       entry_points={
          'console_scripts': [
              'myscript = myscript.cli:PYTHON_ARGCOMPLETE_OK',
          ]
       }
       # ...
    )

And in your module ``myscript.cli``::

    from argdeco import main as PYTHON_ARGCOMPLETE_OK, main

    @main
    def my_main():
       pass

.. _argcomplete: https://github.com/kislyuk/argcomplete
.. _activate global completion: https://github.com/kislyuk/argcomplete#activating-global-completion

Contents
--------

.. toctree::
   :maxdepth: 2

   argdeco
   main
   command_decorator
   arg
   config


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

