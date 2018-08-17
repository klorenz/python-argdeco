
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


def test_main_global_args():
    '''Get the args object as compiled by argparse'''

    result = {}
    main = Main(error_handler=None, compile=True)

    #import rpdb2 ; rpdb2.start_embedded_debugger('foo')

    # add argument in decorator (recommended)
    @main(
        arg('--foo', help="foo arg")
    )
    def _main_func(opts):
        result.update(opts)

    # add arguments separately
    main.add_arguments(
        arg('--bar', help="bar arg")
    )

    # add arguments in call to main function
    main('--foo', 'bar', '--bar', 'glork', '--blub', 'b',
        arg('--blub', help='blub arg')
    )
    assert result['foo'] == 'bar'
    assert result['bar'] == 'glork'
    assert result['blub'] == 'b'

