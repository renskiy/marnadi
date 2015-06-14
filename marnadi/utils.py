import functools
import importlib
import weakref

try:
    unicode_str = unicode
except NameError:
    unicode_str = str


def metaclass(mcs):
    def _decorator(cls):
        attrs = dict(vars(cls))
        try:
            if isinstance(cls.__slots__, str):
                slots = (cls.__slots__, )
            else:
                slots = cls.__slots__
            for slot in slots:
                del attrs[slot]
        except AttributeError:
            pass
        for prop in '__weakref__', '__dict__':
            attrs.pop(prop, None)
        return mcs(cls.__name__, cls.__bases__, attrs)
    return _decorator


class ReferenceType(type):

    def __call__(cls, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            if isinstance(args[0], cls):
                return args[0]
        return super(ReferenceType, cls).__call__(*args, **kwargs)


class CachedDescriptor(object):

    __slots__ = '_cache',

    def __init__(self):
        self._cache = weakref.WeakKeyDictionary()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self  # static access
        try:
            return self._cache[instance]
        except KeyError:
            value = self._cache[instance] = self.get_value(instance)
            return value

    def __set__(self, instance, value):
        self._cache[instance] = self.set_value(instance, value)

    def __delete__(self, instance):
        del self._cache[instance]

    def get_value(self, instance):
        raise NotImplementedError

    def set_value(self, instance, value):
        return value


class cached_property(CachedDescriptor):

    __slots__ = 'get', 'set', '__doc__'

    def __init__(self, fget=None, fset=None, doc=None):
        super(cached_property, self).__init__()
        self.get = fget
        self.set = fset
        self.__doc__ = doc

    def get_value(self, instance):
        if self.get is None:
            raise AttributeError("unreadable attribute")
        return self.get(instance)

    def set_value(self, instance, value):
        if self.set is not None:
            return self.set(instance, value)
        return super(cached_property, self).set_value(instance, value)

    def getter(self, getter):
        self.get = getter
        return self

    def setter(self, setter):
        self.set = setter
        return self


class LazyType(type):

    def __call__(cls, path):
        if isinstance(path, cls) or not isinstance(path, str):
            return path
        return super(LazyType, cls).__call__(path)


@metaclass(LazyType)
class Lazy(object):

    __slots__ = '_path', '__weakref__'

    def __init__(self, path):
        super(Lazy, self).__init__()
        self._path = path

    def __call__(self, *args, **kwargs):
        return self._obj(*args, **kwargs)

    def __iter__(self):
        return iter(self._obj)

    def __len__(self):
        return len(self._obj)

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

    def __bool__(self):
        return bool(self._obj)

    def __nonzero__(self):
        return self.__bool__()

    @property
    def __class__(self):
        return self._obj.__class__

    @cached_property
    def _obj(self):
        if self._path is None:
            return
        try:
            module_name, obj_name = self._path.rsplit('.', 1)
        except ValueError:
            module_name, obj_name = self._path, None
        module = importlib.import_module(module_name)
        if obj_name is not None:
            return getattr(module, obj_name)
        return module


def to_bytes(obj, encoding='utf-8', error_callback=None):
    try:
        if isinstance(obj, (bytes, bytearray, memoryview)):
            return bytes(obj)
        if obj is None:
            return b''
        try:
            return obj.__bytes__()
        except AttributeError:
            return unicode_str(obj).encode(encoding=encoding)
    except Exception as error:
        if error_callback is not None:
            error_callback(error)
        raise


def coroutine(fn):
    @functools.wraps(fn)
    def _fn(*args, **kwargs):
        co = fn(*args, **kwargs)
        co.send(None)
        return co
    return _fn
