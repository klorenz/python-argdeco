"""working with configurations

"""

class Config(dict):
    '''dictionary-like class

    This class implements a dictionary, which creates deep objects from keys
    like "foo.bar".  Example:

    >>> c = Config()
    >>> c['foo.bar'] = 'x'
    >>> c
    {'foo': {'bar': 'x'}}
    >>> c['foo.bar']
    'x'

    '''

    def __getitem__(self, name):
        key_parts = name.split('.')
        value = super(Config, self).__getitem__(key_parts[0])
        for k in key_parts[1:]:
            value = value[k]
        return value

    def __setitem__(self, name, value):
        key_parts = name.split('.')
        val = super(Config, self).__getitem__(key_parts[0])
        for k in key_parts[1:-1]:
            if k not in val:
                val[k] = {}
            val = val[k]
        val[key_parts[-1]] = value

    def __contains__(self, name):
        try:
            self[name]
            return True
        except KeyError:
            return False


def config_factory(ConfigClass=dict):
    '''return a class, which implements the compiler_factory API

    :param ConfigClass:
        defaults to dict.  A simple factory (without parameter) for a
        dictionary-like object, which implements __setitem__() method.

    :returns:
        ConfigFactory class, which implements compiler_factory API.
    '''
    config_factory = ConfigClass

    class ConfigFactory:
        def __init__(self, command):
            self.command = command

        def __call__(self, args, **opts):
            cfg = ConfigClass()

            for k,v in opts.items():
                config_name = self.command.get_config_name(args.action, k)
                cfg[config_name] = v

            return (cfg,)

    return ConfigFactory
