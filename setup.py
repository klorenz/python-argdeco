from distutils.core import setup
from argdeco import __version__

setup(name='argdeco',
  version=__version__,
  #py_modules=['argdeco'],
  packages = ['argdeco'],
  author = 'Kay-Uwe (Kiwi) Lorenz',
  author_email = "kiwi@franka.dyndns.org",
  url = 'https://github.com/klorenz/python-argdeco',
  description = "specify command arguments in function decorator",
  long_description = """
  """,
  keywords = "argument command argparse cli",
  #download_url
  license = "MIT",
)
