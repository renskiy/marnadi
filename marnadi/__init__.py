import importlib
import itertools


class Lazy(object):

    __slots__ = ('_path', '_value')

    def __init__(self, path):
        if isinstance(path, basestring):
            self._value = None
            self._path = path
        else:
            self.obj = path

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def __iter__(self):
        return self.obj.__iter__()

    def __str__(self):
        return str(self.obj)

    def __getitem__(self, item):
        return self.obj[item]

    def __getattr__(self, attr):
        return getattr(self.obj, attr)

    @property
    def obj(self):
        if self._value is None:
            module_name, obj_name = self._path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self.obj = getattr(module, obj_name)
        return self._value

    @obj.setter
    def obj(self, value):
        if value is None:
            raise TypeError("`obj` can't be None")
        self._value = value


class _Route(type):

    def __call__(cls, *args, **kwargs):
        if len(args) < 2:
            raise ValueError(
                "`%s` needs minimum two arguments" % cls.__name__)
        _kwargs = {}
        try:
            _kwargs['path'] = kwargs.pop('path')
        except KeyError:
            pass
        try:
            _kwargs['handler'] = kwargs.pop('handler')
        except KeyError:
            pass
        route = super(_Route, cls).__call__(*args, **kwargs)
        route.kwargs.update(_kwargs)
        return route


class Route(object):

    __slots__ = ('path', '_handler', 'args', 'kwargs')

    __metaclass__ = _Route

    def __init__(self, path, handler, *args, **kwargs):
        self.path = path
        self._handler = Lazy(handler)
        self.args = args
        self.kwargs = kwargs

    @property
    def handler(self):
        return self._handler.obj

    @handler.setter
    def handler(self, value):
        self._handler.obj = value


class Header(object):

    __slots__ = ('values', 'attributes')

    def __init__(self, *values, **attributes):
        self.values = values
        self.attributes = attributes

    def __str__(self):
        return self.make_value(*self.values, **self.attributes)

    @staticmethod
    def make_value(*values, **attributes):
        return '; '.join(itertools.chain(
            values,
            (
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in attributes.iteritems()
            ),
        ))