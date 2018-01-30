import dateutil.parser

from argdeco import arg, command, main

@arg("-d", "--date", help="pass some date")
def arg_date(value):
    # here we can do some validations
    try:
        v = dateutil.parser.parse(value)
        return v
    except StandardError as e:
        raise e

@command("check_date", arg_date)
def check_date(date):
    print(date)

if __name__ == "__main__":
    main()
