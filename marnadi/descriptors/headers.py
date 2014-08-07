import collections
import copy
import itertools

from marnadi.utils import cached_property, CachedDescriptor


class _Headers(collections.Mapping):

    @cached_property
    def _headers(self):
        raise ValueError("This property must be set before using")

    def __getitem__(self, header):
        return self._headers[header.title()]

    def __len__(self):
        return len(self._headers)

    def __iter__(self):
        return iter(self._headers)

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    __ne__ = object.__ne__

    def items(self):
        for header, values in self._headers.items():
            for value in values:
                yield header, value

    def values(self):
        for values in self._headers.values():
            for value in values:
                yield value


class ResponseHeaders(_Headers):
    """Headers - dict-like object which allow to read request
    and set response headers.

    All methods are divided into two groups: getters and setters where
    getters usually provide access to request headers and setters
    allow to modify response headers. For more information see
    particular method description.
    """

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

    # def get_parsed(self, request_header, default=None):
    #     """Parses value and params of complex request headers.
    #
    #     Args:
    #         request_header (str): header name.
    #
    #     Kwargs:
    #         default: default header value.
    #
    #     Returns:
    #         (str, dict). Header value and params dict.
    #
    #     .. warning::
    #         Beware of using header params as kwargs since these params
    #         may be used for data injection into your callable entities.
    #         E.g. `some_function(**params)`.
    #     """
    #
    #     try:
    #         raw_value = self[request_header]
    #     except KeyError:
    #         return default, {}
    #     parts = iter(raw_value.split(';'))
    #     value = next(parts)
    #     return value, dict(
    #         (lambda p, v='': (p, v.strip('"')))(*param.split('=', 1))
    #         for param in filter(str.strip, parts)
    #     )


class Headers(CachedDescriptor, _Headers):

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
