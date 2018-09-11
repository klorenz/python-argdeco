import dateutil.parser
from argdeco import arg, main, mutually_exclusive, opt
from argdeco.main import Main, ArgParseExit
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

def test_mutually_exclusive():
    main = Main(error_handler=None)

    @main(
        mutually_exclusive(
            arg('--foo'),
            arg('--bar'),
        )
    )
    def _main(foo, bar):
        result['foo'] = foo
        result['bar'] = bar

    r = main('--foo', 'a', '--bar', 'b')
    assert isinstance(main.exception, ArgParseExit)

    result = {}
    main('--foo', 'a')
    assert result == {'foo': 'a', 'bar': None}

    result = {}
    main('--bar', 'b')
    assert result == {'foo': None, 'bar': 'b'}

def test_config():
    from argdeco.config import config_factory
    main = Main(error_handler=None, compiler_factory=config_factory(dict))
    remote_command = main.command.add_subcommands('remote')

    results = []
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    @remote_command('add', arg('name'), arg('url'))
    def _remote_add(cfg):
        results.append(cfg)

    @remote_command('rename',
        arg('old_name', config="x.y"),
        arg('new_name'),
        arg('--flag', default='x', config=".foobar"),
        arg('--hidden_flag', default='x', config=None),
        )
    def _remote_rename(cfg):
        results.append(cfg)

    assert main.command['remote.rename'].get_default('action') is _remote_rename
    assert main.command.get_action('remote.rename') is _remote_rename
    assert main.command.get_config_name('remote.rename', 'flag') == 'remote.rename.foobar'

    @main.command('ls', opt('--all'))
    def _ls(cfg):
        results.append(cfg)

    main('remote', 'add', 'foo', 'http://localhost')

    main('remote', 'rename', 'bar', 'x')
    main('ls')
    main('ls', '--all')

    assert results == [
        {'remote.add.name': 'foo', 'remote.add.url': 'http://localhost'},
        {'x.y': 'bar', 'remote.rename.foobar': 'x', 'remote.rename.new_name': 'x'},
        {'ls.all': False},
        {'ls.all': True},
    ]

