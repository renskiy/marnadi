import re

from marnadi.utils import Lazy

pattern_type = type(re.compile(''))


class Route(object):

    __slots__ = 'path', 'handler', 'params', 'pattern'

    placeholder_re = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    def __init__(self, path, handler, params=None):
        self.path = path
        self.handler = Lazy(handler)
        self.params = params or {}
        self.pattern = self.make_pattern(path)

    def match(self, request_path):
        pattern = self.pattern or self.path
        if isinstance(pattern, pattern_type):
            match = pattern.match(request_path)
            if match:
                return request_path[match.end(0):], match.groupdict()
        elif request_path.startswith(pattern):
            return request_path[len(pattern):], ()

    @classmethod
    def make_pattern(cls, path):
        if isinstance(path, pattern_type):
            return
        unescaped_path = path.replace('{{', '').replace('}}', '')
        placeholders = cls.placeholder_re.findall(unescaped_path)
        if not placeholders:
            return
        pattern = re.escape(path.replace('{{', '{').replace('}}', '}'))
        for placeholder in placeholders:
            pattern = pattern.replace(
                '\\{{{}\\}}'.format(placeholder),
                '(?P<{}>.+)'.format(placeholder),
            )
        return re.compile(pattern)

    def restore_path(self, **params):
        if isinstance(self.path, pattern_type):
            raise TypeError("can't restore path from native regular expression")
        return self.path.format(**params)


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
