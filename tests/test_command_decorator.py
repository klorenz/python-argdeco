def test_config_arg():
    from argdeco import CommandDecorator, arg
    from argdeco.config import config_factory

    command = CommandDecorator(compiler_factory=config_factory())

    @command('foo', arg('--first'), arg('--second', default=1, config_name="foo.bar"))
    def cmd_foo(config):
        assert config['foo.first'] == '1'
        assert config['foo.bar'] == 1

    assert command.get_config_name(cmd_foo, 'first') == "foo.first"

    command.execute(['foo', '--first', '1'])