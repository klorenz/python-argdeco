.. argdeco documentation master file, created by
   sphinx-quickstart on Fri Aug 17 10:11:19 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. highlight:: py

argdeco -- command line interfaces with decorators
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


Quickstart
----------

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

Contents:

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

