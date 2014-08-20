import re

from marnadi.utils import Lazy


class Route(object):

    __slots__ = 'path', 'handler', 'params', 'pattern', 'name'

    placeholder_re = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    def __init__(self, path, handler, name=None, params=None, patterns=None):
        self.path = path
        self.handler = Lazy(handler)
        self.name = name
        self.params = params or {}
        self.pattern = self.make_pattern(path, patterns)

    def match(self, request_path):
        if self.pattern is not None:
            match = self.pattern.match(request_path)
            if match:
                return request_path[match.end(0):], match.groupdict()
        elif request_path.startswith(self.path):
            return request_path[len(self.path):], ()

    @classmethod
    def make_pattern(cls, path, placeholder_patterns=None):
        unescaped_path = path.replace('{{', '').replace('}}', '')
        placeholders = cls.placeholder_re.findall(unescaped_path)
        if not placeholders:
            return
        placeholder_patterns = placeholder_patterns or {}
        pattern = re.escape(path.replace('{{', '{').replace('}}', '}'))
        for placeholder in placeholders:
            pattern = pattern.replace(
                r'\{{{placeholder}\}}'.format(placeholder=placeholder),
                r'(?P<{name}>{pattern})'.format(
                    name=placeholder,
                    pattern=placeholder_patterns.get(placeholder, r'\w+')
                ),
            )
        return re.compile(pattern)

    def restore_path(self, **params):
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
