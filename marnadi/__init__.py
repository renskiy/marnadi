import functools
import importlib


class Lazy(object):

    __slots__ = ('_obj', 'args', 'kwargs')

    def __init__(self, obj, *args, **kwargs):
        self._obj = obj
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def __iter__(self):
        return self.obj.__iter__()

    @property
    def obj(self):
        if isinstance(self._obj, basestring):
            module_name, obj_name = self._obj.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self._obj = obj = getattr(module, obj_name)
            if callable(obj):
                self._obj = functools.partial(obj, *self.args, **self.kwargs)
        return self._obj