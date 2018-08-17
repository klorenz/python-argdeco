import dateutil.parser
from argdeco import arg, main
from argdeco.main import Main
from datetime import datetime


def test_date_1():
    main = Main(error_handler=None)
    command = main.command

    @arg("-d", "--date", help="pass some date")
    def arg_date(value):
        # here we can do some validations
        try:
            v = dateutil.parser.parse(value)
            print(v)
            return v
        except StandardError as e:
            raise e

    result = {}

    @main(arg_date)
    def check_date(date):
        print(date)
        result['date'] = date

    main('-d', '2018-01-01')
    assert result['date'] == datetime(2018, 1, 1)


def test_date_2():
    main = Main(error_handler=None)
    command = main.command

    @arg("-d", "--date", help="pass some date")
    def arg_date(self, parser, namespace, values, option_string=None):
      # here we can do some validations
      setattr(namespace, self.dest, dateutil.parser.parse(values))

    result = {}

    @main(arg_date)
    def _main(date):
        result['date'] = date

    main('-d', '2018-01-01')
    assert result['date'] == datetime(2018, 1, 1)



def test_date_3():
    main = Main(error_handler=None)
    command = main.command

    @arg("-d", "--date", help="pass some date")
    def arg_date(value):
        # here we can do some validations
        return dateutil.parser.parse(value)

    result = {}

    @main(arg_date)
    def check_date(date):
        result['date'] = date

    main('-d', '2018-01-01')
    assert result['date'] == datetime(2018, 1, 1)

    main('-d', 'foobar')
    assert isinstance(main.exception, ValueError)
