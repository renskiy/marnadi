import importlib
import itertools


def metaclass(mcs):
    def _decorator(cls):
        attrs = dict(cls.__dict__)
        for prop in ('__weakref__', '__dict__'):
            try:
                del attrs[prop]
            except KeyError:
                pass
        return mcs(cls.__name__, cls.__bases__, attrs)
    return _decorator


class LazyType(type):

    def __call__(cls, path):
        if isinstance(path, cls):
            return path
        elif isinstance(path, str):
            return super(LazyType, cls).__call__(path)
        return path


@metaclass(LazyType)
class Lazy(object):

    def __init__(self, path):
        self._value = None
        self._value_set = False
        self._path = path

    def __call__(self, *args, **kwargs):
        return self._obj(*args, **kwargs)

    def __iter__(self):
        return self._obj.__iter__()

    def __str__(self):
        return str(self._obj)

    def __unicode__(self):
        return unicode(self._obj)

    def __bytes__(self):
        return bytes(self._obj)

    def __getitem__(self, item):
        return self._obj[item]

    def __getattr__(self, attr):
        return getattr(self._obj, attr)

    @property
    def __class__(self):
        return self._obj.__class__

    @property
    def _obj(self):
        if not self._value_set:
            try:
                module_name, obj_name = self._path.rsplit('.', 1)
            except ValueError:
                module_name, obj_name = self._path, None
            module = importlib.import_module(module_name)
            self._value = obj_name and getattr(module, obj_name) or module
            self._value_set = True
        return self._value


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
        return self.make_value(*self.values, **self.attributes)

    @staticmethod
    def make_value(*values, **attributes):
        return '; '.join(itertools.chain(
            values,
            (
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in attributes.items()
            ),
        ))


class cached_property(object):

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.get = fget
        self.set = fset
        self.delete = fdel
        self.__doc__ = doc

    def __get__(self, instance, instance_type=None):
        if self.get is None:
            raise AttributeError('unreadable attribute')
        try:
            return instance.__dict__[self.get.__name__]
        except KeyError:
            pass
        result = instance.__dict__[self.get.__name__] = self.get(instance)
        return result

    def __set__(self, instance, value):
        if self.set is None:
            raise AttributeError('can\'t set attribute')
        self.set(instance, value)

    def __delete__(self, instance):
        if self.delete is None:
            raise AttributeError('can\'t delete attribute')
        self.delete(instance)

    def getter(self, getter):
        self.get = getter

    def setter(self, setter):
        self.set = setter

    def deleter(self, deleter):
        self.delete = deleter
