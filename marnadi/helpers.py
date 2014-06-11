import itertools

from marnadi.utils import metaclass, Lazy


class RouteType(type):

    def __call__(cls, *args, **kwargs):
        if len(args) < 2:
            raise ValueError(
                "`%s` needs minimum two arguments" % cls.__name__)
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

    def __init__(self, path, handler, *args, **kwargs):
        self.path = path
        self.handler = Lazy(handler)
        self.args = args
        self.kwargs = kwargs


class Header(object):

    def __init__(self, *values, **attributes):
        self.values = values
        self.attributes = attributes

    def __str__(self):
        return self.make_value()

    def __bytes__(self):
        value = self.make_value()
        if isinstance(value, bytes):  # python 2.x
            return value
        return value.encode(encoding='latin1')

    def make_value(self):
        return '; '.join(itertools.chain(
            self.values,
            (
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in self.attributes.items()
            ),
        ))
