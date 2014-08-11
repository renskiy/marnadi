from marnadi.utils import Lazy


class Route(object):

    __slots__ = 'path', 'handler', 'args', 'kwargs'

    def __init__(self, _path, _handler, *args, **kwargs):
        self.path = _path
        self.handler = Lazy(_handler)
        self.args = args
        self.kwargs = kwargs


class Header(object):

    __slots__ = 'value', 'params'

    def __init__(self, _value, **params):
        self.value = _value
        self.params = params

    def __str__(self):
        return self.make_value()

    def __bytes__(self):
        value = self.make_value()
        if isinstance(value, bytes):  # python 2.x
            return value
        return value.encode(encoding='latin1')

    def make_value(self):
        if not self.params:
            return str(self.value)
        return '{value}; {params}'.format(
            value=self.value,
            params='; '.join(
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in self.params.items()
            ),
        )
