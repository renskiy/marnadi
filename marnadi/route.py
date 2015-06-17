import re

from marnadi.utils import ReferenceType, metaclass, Lazy


class Route(object):

    __slots__ = 'path', 'handler', 'params', 'pattern', 'name', 'callbacks', \
                'routes'

    placeholder_re = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    def __init__(self, path, handler=None, routes=(), name=None, params=None,
                 callbacks=None, patterns=None):
        self.path = path
        self.handler = Lazy(handler)
        self.routes = Routes(routes)
        self.name = name
        self.params = params or {}
        self.callbacks = callbacks or {}
        self.pattern = self.make_pattern(patterns)

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)

    def match(self, path):
        if self.pattern:
            match = self.pattern.match(path)
            if match:
                params = {
                    param: self.callbacks.get(param, lambda x: x)(value)
                    for param, value in match.groupdict().items()
                }
                return path[match.end(0):], dict(self.params, **params)
        elif path.startswith(self.path):
            return path[len(self.path):], self.params

    def make_pattern(self, patterns=None):
        unescaped_path = self.path.replace('{{', '').replace('}}', '')
        placeholders = self.placeholder_re.findall(unescaped_path)
        if not placeholders:
            return
        patterns = patterns or {}
        pattern = re.escape(self.path.replace('{{', '{').replace('}}', '}'))
        for placeholder in placeholders:
            pattern = pattern.replace(
                r'\{{{placeholder}\}}'.format(placeholder=placeholder),
                r'(?P<{name}>{pattern})'.format(
                    name=placeholder,
                    pattern=patterns.get(placeholder, r'\w+')
                ),
            )
        return re.compile(pattern)

    def restore_path(self, **params):
        return self.path.format(**params)


@metaclass(ReferenceType)
class Routes(list):

    __slots__ = ()

    def __init__(self, seq=()):
        def unnest(routes):
            for route in map(Lazy, routes):
                if isinstance(route, Route):
                    yield route
                else:
                    for unnested in unnest(route):
                        yield unnested
        super(Routes, self).__init__(unnest(seq))

    def route(self, path, **route_params):
        def _decorator(handler):
            self.append(Route(path, handler, **route_params))
            return handler
        return _decorator
