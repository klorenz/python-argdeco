import dateutil.parser

from argdeco import arg, command, main

@arg("-d", "--date", help="pass some date")
def arg_date(self, parser, namespace, values, option_string=None):
  # here we can do some validations
  print "self: %s" % self
  setattr(namespace, self.dest, dateutil.parser.parse(values))

@command("check_date", arg_date)
def check_date(date):
  print(date)

main()
