import collections

from marnadi.http.data import Data
from marnadi.http.cookies import Cookies
from marnadi.http.headers import Headers


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
