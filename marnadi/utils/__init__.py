import functools

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
                if slot.startswith('__') and not slot.endswith('__'):
                    slot = '_{cls}{slot}'.format(cls=cls.__name__, slot=slot)
                attrs.pop(slot, None)
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

from .lazy import Lazy, CachedDescriptor, cached_property
