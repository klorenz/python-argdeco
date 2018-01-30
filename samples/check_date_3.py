import dateutil.parser

from argdeco import arg, command, main

@arg("date", help="pass some date")
def arg_date(value):
    # here we can do some validations
    return dateutil.parser.parse(value)

@main(arg_date)
def check_date(date):
    print(date)

main()
