def test_config_class():
    from argdeco import ConfigDict

    x = ConfigDict({'foo': {'bar': 'glork'}}).update({'foo': {'blub': 'bla'}})
    assert x == {
        'foo': {
            'bar': 'glork',
            'blub': 'bla'
        }
    }

    assert x['foo.bar'] == 'glork'

    x['foo.x.y'] = 'y'
    assert x['foo']['x']['y'] == 'y'
    assert x['foo.x.y'] == 'y'

    assert 'foo.x.y' in x
    assert 'foo.x.z' not in x

    x['a'] = 'b'
    assert x['a'] == 'b'


#def test_config_factory():
