import collections
import copy
import itertools

from marnadi.utils import cached_property, CachedDescriptor


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

    @cached_property
    def _modified_headers(self):
        modified_headers = self._headers = copy.copy(self._headers)
        return modified_headers

    def __delitem__(self, header):
        del self._modified_headers[header.title()]

    def __setitem__(self, header, value):
        self._modified_headers[header.title()] = [value]

    def append(self, header, value):
        self._modified_headers[header.title()].append(value)

    def extend(self, *headers):
        for header in headers:
            self.append(*header)

    def setdefault(self, header, default=None):
        return self._modified_headers.setdefault(header.title(), [default])

    def clear(self, *headers):
        if headers:
            for header in headers:
                try:
                    del self[header]
                except KeyError:
                    pass
        else:
            self._modified_headers.clear()


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
        return ResponseHeaders(default_headers=self._headers)
