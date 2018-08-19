"""Working with configurations

A common pattern making use of configuration files::

    from argdeco import main, command, arg, opt, config_factory
    form os.path import expanduser

    main.configure(compiler_factory=config_factory(
        config_file=arg('--config-file', '-C', help="configuration file", default=expanduser('~/.config/myconfig.yaml'))
    ))

    @command('ls', opt('--all'))
    def mycmd(cfg):
        if cfg['ls.all']:
            pass

    main()

If you want to have ``foo.bar`` expanded to ``{'foo': {'bar': ...}}``, use
following::

    from argdeco import main, command, arg, opt, config_factory, ConfigDict
    form os.path import expanduser

    main.configure(compiler_factory=config_factory(ConfigDict,
        config_file=arg('--config-file', '-C', help="configuration file", default=expanduser('~/.config/myconfig.yaml'))
    ))

    @command('ls', opt('--all'))
    def mycmd(cfg):
        if cfg['ls']['all']:
            pass

    main()


"""

class ConfigDict(dict):
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
        value = super(ConfigDict, self).__getitem__(key_parts[0])
        for k in key_parts[1:]:
            value = value[k]
        return value

    def __setitem__(self, name, value):
        key_parts = name.split('.')
        val = super(ConfigDict, self).__getitem__(key_parts[0])
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


    def flatten(self, D):
        '''flatten a nested dictionary D to a flat dictionary

        nested keys are separated by '.'
        '''

        if not isinstance(D, dict):
            return D

        result = {}
        for k,v in D.items():
            if isinstance(v, dict):
                for _k,_v in self.flatten(v).items():
                    result['.'.join([k,_k])] = _v
            else:
                result[k] = v
        return result


    def update(self, E=None, **F):
        '''flatten nested dictionaries to update pathwise

        >>> Config({'foo': {'bar': 'glork'}}).update({'foo': {'blub': 'bla'}})
        {'foo': {'bar': 'glork', 'blub': 'bla'}

        In contrast to:

        >>> {'foo': {'bar': 'glork'}}.update({'foo': {'blub': 'bla'}})
        {'foo: {'blub': 'bla'}'}

        '''
        if E is not None:
            if not hasattr(E, 'keys'):
                E = dict(E)
            for k,v in self.flatten(E).items():
                self[k] = v

        for k,v in self.flatten(F).items():
            self[k] = v

        return self



def config_factory(ConfigClass=dict, prefix=None,
    config_file=None
    ):
    '''return a class, which implements the compiler_factory API

    :param ConfigClass:
        defaults to dict.  A simple factory (without parameter) for a
        dictionary-like object, which implements __setitem__() method.

        Additionally you can implement following methods:

        :``init_args``: A method to be called to initialize the config object
           by passing :py:class:`~argparse.Namespace` object resulting from
           :py:class:`~argparse.ArgumentParser.parseargs` method.

           You could load data from a configuration file here.

    :param prefix:
        Add this prefix to config_name.  (e.g. if prefix="foo" and you
        have config_name="x.y" final config_path results in "foo.x.y")

    :param config_file:
        An :py:class:`~argdeco.arguments.arg` to provide a config file.

        If you provide this argument, you can implement one of the following
        methods in your ``ConfigClass`` to load data from the configfile:

        :``load``: If you pass ``config_file`` argument, this method can be
           implemented to load configuration data from resulting stream.

           If config_file is '-', stdin stream is passed.

        :``load_from_file``: If you prefer to open the file yourself, you can
           do this, by implementing ``load_from_file`` instead which has the
           filename as its single argument.

        :``update``: method like :py:meth:`dict.update`.   If neither of
           ``load`` or ``load_from_file`` is present, but ``update`` is,
           it is assumed, that config_file is of type YAML (or JSON) and
           configuration is updated by calling ``update`` with the parsed data
           as parameter.

        If you implement neither of these, it is assumed, that configuration
        file is of type YAML (or plain JSON, as YAML is a superset of it).

        Data is loaded from file and will update configuration object using
        dict-like :py:meth:`dict.update` method.

    :type config_file: argdeco.arguments.arg

    :returns:
        ConfigFactory class, which implements compiler_factory API.
    '''
    config_factory = ConfigClass

    class ConfigFactory:
        def __init__(self, command):
            self.command = command
            if config_file:
                assert isinstance(config_file, arg), "config_file must be of type arg"
                try:
                    self.command.add_argument(config_file)
                except:
                    pass

        def __call__(self, args, **opts):
            cfg = ConfigClass()

            if hasattr(cfg, 'init_args'):
                cfg.init_args(args)

            if config_file is not None:
                fn = getattr(args, config_file.dest)
                if hasattr(cfg, 'load'):
                    if config_file.dest == '-':
                        cfg.load(sys.stdin)
                    else:
                        with open(fn, 'r') as f:
                            cfg.load(f)

                elif hasattr(cfg, 'load_from_file'):
                    cfg.load_from_file(fn)

                elif hasattr(cfg, 'update'):
                    # assume yaml file
                    import yaml
                    with open(fn, 'r') as f:
                        data = yaml.load(f)
                    cfg.update(data)

            for k,v in opts.items():
                config_name = self.command.get_config_name(args.action, k)

                if config_name is None: continue
                if prefix is not None:
                    config_name = '.'.join([prefix, config_name])
                cfg[config_name] = v

            return (cfg,)

    return ConfigFactory
