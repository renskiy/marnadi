import re

from marnadi.utils import Lazy

pattern_type = type(re.compile(''))


class Route(object):

    __slots__ = 'path', 'handler', 'params'

    def __init__(self, path, handler, params=None):
        self.path = path
        self.handler = Lazy(handler)
        self.params = params or {}

    def match(self, path):
        if isinstance(self.path, pattern_type):
            match = self.path.match(path)
            if match:
                return path[match.end(0):], match.groupdict()
        elif path.startswith(self.path):
            return path[len(self.path):], ()


class Header(object):

    __slots__ = 'value', 'params'

    def __init__(self, _value, **params):
        self.value = _value
        self.params = params

    def __str__(self):
        return self.make_value()

    def __bytes__(self):
        value = self.make_value()
        if isinstance(value, bytes):  # python 2.x
            return value
        return value.encode(encoding='latin1')

    def make_value(self):
        if not self.params:
            return str(self.value)
        return '{value}; {params}'.format(
            value=self.value,
            params='; '.join(
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in self.params.items()
            ),
        )
