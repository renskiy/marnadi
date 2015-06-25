import weakref

from marnadi.utils import metaclass


class CachedDescriptor(object):

    __slots__ = 'cache',

    def __init__(self):
        self.cache = weakref.WeakKeyDictionary()

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self  # static access
        try:
            return self.cache[instance]
        except KeyError:
            value = self.cache[instance] = self.get_value(instance)
            return value

    def __set__(self, instance, value):
        self.cache[instance] = self.set_value(instance, value)

    def __delete__(self, instance):
        del self.cache[instance]

    def get_value(self, instance):
        raise NotImplementedError

    def set_value(self, instance, value):
        return value


class CachedProperty(CachedDescriptor):

    __slots__ = 'get', 'set', '__doc__'

    def __init__(self, fget=None, fset=None, doc=None):
        super(CachedProperty, self).__init__()
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
        return super(CachedProperty, self).set_value(instance, value)

    def getter(self, getter):
        self.get = getter
        return self

    def setter(self, setter):
        self.set = setter
        return self

cached_property = CachedProperty


class LazyMeta(type):

    def __call__(cls, path):
        if isinstance(path, cls) or not isinstance(path, str):
            return path
        return super(LazyMeta, cls).__call__(path)


@metaclass(LazyMeta)
class Lazy(object):

    __slots__ = '__path', '__weakref__', '__class__'

    def __init__(self, path):
        super(Lazy, self).__init__()
        self.__path = path

    def __call__(self, *args, **kwargs):
        return self.__obj(*args, **kwargs)

    def __iter__(self):
        return iter(self.__obj)

    def __len__(self):
        return len(self.__obj)

    def __str__(self):
        return str(self.__obj)

    def __unicode__(self):
        return unicode(self.__obj)

    def __bytes__(self):
        return bytes(self.__obj)

    def __getitem__(self, item):
        return self.__obj[item]

    def __getattr__(self, attr):
        return getattr(self.__obj, attr)

    def __bool__(self):
        return bool(self.__obj)

    def __nonzero__(self):
        return self.__bool__()

    @cached_property
    def __obj(self):
        package, _, attribute = self.__path.rpartition('.')
        if not package:
            package, attribute = attribute, package
        module = package.rpartition('.')[2]
        imported = __import__(package, fromlist=(module, ))
        if attribute:
            return getattr(imported, attribute)
        return imported
