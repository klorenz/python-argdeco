def test_config_class():
    from argdeco import ConfigDict

    x = ConfigDict({'foo': {'bar': 'glork'}})
    assert isinstance(x['foo'], ConfigDict)
    x['foo'].an_attr = 'a_value'
    assert x['foo'].an_attr == 'a_value'

#    import rpdb2 ; rpdb2.start_embedded_debugger('foo')

    x.update({'foo': {'blub': 'bla'}})

    assert hasattr(x['foo'], 'an_attr')
    assert x['foo'].an_attr == 'a_value'

    assert x == {
        'foo': {
            'bar': 'glork',
            'blub': 'bla'
        }
    }

    x['foo'].an_attr = 'foo'

    assert x['foo.bar'] == 'glork'

    x['foo.x.y'] = 'y'
    assert x['foo']['x']['y'] == 'y'
    assert x['foo.x.y'] == 'y'

    assert 'foo.x.y' in x
    assert 'foo.x.z' not in x

    x['a'] = 'b'
    assert x['a'] == 'b'

    x['x.y'] = 'z'
    assert x['x.y'] == 'z'

    assert x['foo'].an_attr == 'foo'

#def test_config_factory():
