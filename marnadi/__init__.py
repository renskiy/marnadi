import importlib


class Lazy(object):

    __slots__ = ('_path', '_value')

    def __init__(self, path=None):
        self._path = path
        self._value = None

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

    def __get__(self, instance, owner):
        if not issubclass(owner, Route):
            return self.obj
        route = instance
        value = (
            route.original_handler.obj
            if isinstance(route.original_handler, Lazy) else
            route.original_handler
        )
        route.handler = value
        return value

    @property
    def obj(self):
        if self._value is None:
            module_name, obj_name = self._path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self._value = getattr(module, obj_name)
        return self._value


class Route(object):

    handler = Lazy()

    def __init__(self, path, handler, *args, **kwargs):
        self.path = path
        self.original_handler = handler
        self.args = args
        self.kwargs = kwargs
