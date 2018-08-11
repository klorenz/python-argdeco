
from argdeco.main import Main
from argdeco import arg

def test_main():
    result = {}
    main = Main(error_handler=None, compile=True)

    @main.command('foo', arg('--config', '-c', help="config"))
    def foo(cfg):
        result['cfg'] = cfg

    main('--debug', 'foo', "-c", "foo.cfg", debug=True)
    assert result == {'cfg': {'config': 'foo.cfg'}}

