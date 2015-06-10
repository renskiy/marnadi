import collections
import re

from marnadi.utils import Lazy, ReferenceType, metaclass


class Route(object):

    __slots__ = 'path', 'params', 'pattern', 'name', 'callbacks', \
                'subroutes', '__weakref__'

    placeholder_re = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    handler = Lazy()

    def __init__(self, path, handler=None, subroutes=(), name=None, params=None,
                 callbacks=None, patterns=None):
        self.path = path
        self.handler = handler
        self.subroutes = Routes(map(Lazy, subroutes))
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


def route(path, **route_params):
    def _route(handler):
        return Route(path, handler, **route_params)
    return _route


@metaclass(ReferenceType)
class Routes(list):

    __slots__ = ()

    def route(self, path, **route_params):
        def _decorator(handler):
            self.append(Route(path, handler, **route_params))
            return handler
        return _decorator


class Header(collections.Mapping):

    __slots__ = 'value', 'params'

    def __init__(self, *value, **params):
        assert len(value) == 1
        self.value = value[0]
        self.params = params

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __str__(self):
        return self.stringify()

    def __bytes__(self):
        value = self.stringify()
        if isinstance(value, bytes):  # python 2.x
            return value
        return value.encode(encoding='latin1')

    def __getitem__(self, item):
        return self.params[item]

    def __iter__(self):
        return iter(self.params)

    def __len__(self):
        len(self.params)

    def stringify(self):
        if not self.params:
            return str(self.value)
        return '{value}; {params}'.format(
            value=self.value,
            params='; '.join(
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in self.params.items()
            ),
        )
