import functools
import importlib


class Lazy(object):

    __slots__ = ('path', 'value', 'args', 'kwargs')

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.value = None
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def __iter__(self):
        return self.obj.__iter__()

    def __str__(self):
        return str(self.obj)

    def __getitem__(self, item):
        return self.obj[item]

    def keys(self):
        return self.obj.iterkeys()

    @property
    def obj(self):
        if self.value is None:
            module_name, obj_name = self.path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            value = getattr(module, obj_name)
            if callable(value):
                value = functools.partial(value, *self.args, **self.kwargs)
            self.value = value
        return self.value