from distutils.core import setup
from argdeco import __version__
from textwrap import dedent

setup(name='argdeco',
  version=__version__,
  #py_modules=['argdeco'],
  packages = ['argdeco'],
  author = 'Kay-Uwe (Kiwi) Lorenz',
  author_email = "kiwi@franka.dyndns.org",
  url = 'https://github.com/klorenz/python-argdeco',
  description = "specify command arguments in function decorator",
  install_requires=[
    'argcomplete'
  ],
  long_description = dedent("""\
     argdeco
     =======

     Specify command line arguments using decorators::

         from argdeco import main, arg, opt

         @main(
            arg("--foo", help="some argument"),
            opt("--flag", '-f', help="toggle flag"),
         )
         def my_main_function(foo, flag):
             return 0  # success, will be exit code

         if __name__ == '__main__':
             main()

     argdeco is an argparse wrapper.

     * ``arg()`` is only a wrapper around ``argparse.ArgumentParser.add_argument()``.
     * ``opt()`` is a shorthand for ``arg(..., action=store_true, default=False)``

     ... you can do `much more`_

     .. [much more] https://python-argdeco.readthedocs.io

  """),
  keywords = "argument command argparse cli",
  #download_url
  license = "MIT",
)
