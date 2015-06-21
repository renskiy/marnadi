import collections
import itertools

from marnadi.utils import cached_property, CachedDescriptor


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
        return len(self.params)

    def __bool__(self):
        return True

    def __nonzero__(self):
        return self.__bool__()

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


class HeadersMixin(collections.Mapping):

    if hasattr(collections.Mapping, '__slots__'):
        __slots__ = '__weakref__',

    def __getitem__(self, header):
        return self._headers[header.title()]

    def __len__(self):
        return len(self._headers)

    def __iter__(self):
        return iter(self._headers)

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    __ne__ = object.__ne__

    @cached_property
    def _headers(self):
        raise ValueError("This property must be set before using")

    def items(self, stringify=False):
        for header, values in self._headers.items():
            for value in values:
                yield header, str(value) if stringify else value

    def values(self, stringify=False):
        for values in self._headers.values():
            for value in values:
                yield str(value) if stringify else value


class ResponseHeaders(HeadersMixin, collections.MutableMapping):

    __slots__ = ()

    def __init__(self, default_headers):
        self._headers = default_headers

    def __delitem__(self, header):
        del self._headers[header.title()]

    def __setitem__(self, header, value):
        self._headers[header.title()] = [value]

    def append(self, header_item):
        header, value = header_item
        self._headers[header.title()].append(value)

    def extend(self, headers):
        for header in headers:
            self.append(header)

    def setdefault(self, header, default=None):
        return self._headers.setdefault(header.title(), [default])

    def clear(self, *headers):
        if headers:
            for header in headers:
                try:
                    del self[header]
                except KeyError:
                    pass
        else:
            self._headers.clear()


class Headers(CachedDescriptor, HeadersMixin):

    __slots__ = ()

    def __init__(self, *default_headers, **kw_default_headers):
        super(Headers, self).__init__()
        self._headers = collections.defaultdict(list)
        for header, value in itertools.chain(
            default_headers,
            kw_default_headers.items(),
        ):
            self._headers[header.title()].append(value)

    def get_value(self, instance):
        return ResponseHeaders(default_headers=self._headers.copy())
