import importlib

try:
    unicode_str = unicode
except NameError:
    unicode_str = str


class Empty(object):

    pass


def metaclass(mcs):
    def _decorator(cls):
        attrs = dict(cls.__dict__)
        try:
            if isinstance(cls.__slots__, str):
                slots = cls.__slots__,
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


class cached_property(object):

    __slots__ = ('get', 'set', 'delete', '__doc__', 'cache', 'updated_classes')

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.get = fget
        self.set = fset
        self.delete = fdel
        self.__doc__ = doc
        self.cache = {}
        self.updated_classes = set()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        if self.get is None:
            raise AttributeError("unreadable attribute")
        cache_key = self.make_cache_key(instance)
        try:
            return self.cache[cache_key]
        except KeyError:
            result = self.cache[cache_key] = self.get(instance)
            self.update_destructor(instance)
        return result

    def __set__(self, instance, value):
        if self.set is None:
            raise AttributeError("can't set attribute")
        self.cache.pop(self.make_cache_key(instance), None)
        self.set(instance, value)

    def __delete__(self, instance):
        if self.delete is None:
            raise AttributeError("can't delete attribute")
        self.delete(instance)
        self.cache.pop(self.make_cache_key(instance), None)

    def getter(self, getter):
        self.get = getter
        return self

    def setter(self, setter):
        self.set = setter
        return self

    def deleter(self, deleter):
        self.delete = deleter
        return self

    @staticmethod
    def make_cache_key(instance):
        return id(instance)

    def make_new_destructor(self, old_destructor=None):
        def __del__(inst):
            if old_destructor is not None:
                old_destructor(inst)
            self.cache.pop(self.make_cache_key(inst), None)
        return __del__

    def update_destructor(self, instance):
        instance_class = type(instance)
        if instance_class in self.updated_classes:
            return
        old_destructor = getattr(instance_class, '__del__', None)
        instance_class.__del__ = self.make_new_destructor(old_destructor)
        self.updated_classes.add(instance_class)


class LazyType(type):

    def __call__(cls, path):
        if isinstance(path, cls):
            return path
        elif isinstance(path, str):
            return super(LazyType, cls).__call__(path)
        return path


@metaclass(LazyType)
class Lazy(object):

    __slots__ = ('_path', '__weakref__')

    def __init__(self, path):
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

    @property
    def __class__(self):
        return self._obj.__class__

    @cached_property
    def _obj(self):
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
