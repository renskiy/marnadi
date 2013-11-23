import importlib


class Lazy(object):

    __slots__ = '_obj'

    def __init__(self, obj):
        self._obj = obj

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def __iter__(self):
        return self.obj.__iter__()

    @property
    def obj(self):
        if isinstance(self._obj, basestring):
            module_name, obj_name = self._obj.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self._obj = getattr(module, obj_name)
        return self._obj