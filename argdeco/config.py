from .arguments import arg

class config_arg(arg):
    pass

class Config:
    def __init__(self, **args):
        self.args = args

    def __getattr__(self, name):
        if name == 'config':
            self.config = self.readConfig()

class ConfigManager:

    def config_factory(self, args, **kwargs):
        return [Config(**vars(args))], {}

    def register_config(self, context, argument):
        pass

    def init_config_command(self, command):
        @command( 'config',
            arg('-i', '--interactive', action="store_true", help="do interactive configuration")
            #arg('--set', )
        )
        def cmd_config(config):
            """Set or get configuration

            """

            config_name = config.get('config_name', 'default')
            config_file = config.get('config_file')

            if config_file is None:
                config_file = ()

                #command.

            #config_

#            if config.interactive:
#                for name,
