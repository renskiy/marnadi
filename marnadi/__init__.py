import importlib


class Lazy(object):

    __slots__ = 'obj'

    def __init__(self, obj):
        self.obj = obj

    def __call__(self, *args, **kwargs):
        if isinstance(self.obj, basestring):
            module_name, obj_name = self.obj.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self.obj = getattr(module, obj_name)
        return self.obj(*args, **kwargs)