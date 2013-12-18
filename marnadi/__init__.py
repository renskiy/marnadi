import functools
import importlib


class Lazy(object):

    __slots__ = ('_path', '_value', '_args', '_kwargs')

    def __init__(self, path, *args, **kwargs):
        self._path = path
        self._value = None
        self._args = args
        self._kwargs = kwargs

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
            value = getattr(module, obj_name)
            if callable(value):
                value = functools.partial(value, *self._args, **self._kwargs)
            self._value = value
        return self._value