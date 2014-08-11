from marnadi.utils import metaclass, Lazy


class RouteType(type):

    def __call__(cls, *args, **kwargs):
        if len(args) < 2:
            raise TypeError("needs two arguments")
        _kwargs = {}
        for kwarg in ('path', 'handler'):
            try:
                _kwargs[kwarg] = kwargs.pop(kwarg)
            except KeyError:
                pass
        route = super(RouteType, cls).__call__(*args, **kwargs)
        route.kwargs.update(_kwargs)
        return route


@metaclass(RouteType)
class Route(object):

    __slots__ = 'path', 'handler', 'args', 'kwargs'

    def __init__(self, path, handler, *args, **kwargs):
        self.path = path
        self.handler = Lazy(handler)
        self.args = args
        self.kwargs = kwargs


class Header(object):

    __slots__ = 'value', 'params'

    def __init__(self, *value, **params):
        if len(value) != 1:
            raise TypeError("single header should contain single value")
        self.value = value[0]
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
