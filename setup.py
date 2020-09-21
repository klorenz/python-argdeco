from distutils.core import setup
from argdeco import __version__
from textwrap import dedent

with open('README.md', 'r') as f:
    long_description = f.read()

setup(name='argdeco',
  version=__version__,
  #py_modules=['argdeco'],
  packages = ['argdeco'],
  author = 'Kay-Uwe (Kiwi) Lorenz',
  author_email = "tabkiwi@gmail.com",
  url = 'https://github.com/klorenz/python-argdeco',
  description = "specify command arguments in function decorator",
  install_requires=[
    'argcomplete'
  ],
  #long_description_content_type = "text/markdown",
  long_description_content_type = "text/plain",
 # long_description = long_description,
 long_description = "see github for docs: https://github.com/klorenz/python-argdeco",
  keywords = "argument command argparse cli",
  #download_url
  license = "MIT",
)
