import collections
import itertools

from marnadi.descriptors import Descriptor
from marnadi.utils import cached_property, to_bytes


class Headers(Descriptor, collections.MutableMapping):
    """Headers - dict-like object which allow to read request
    and set response headers.

    All methods are divided into two groups: getters and setters where
    getters usually provide access to request headers and setters
    allow to modify response headers. For more information see
    particular method description.
    """

    def __init__(self, *default_headers):
        super(Headers, self).__init__()
        self.response_headers = collections.defaultdict(list)
        self.extend(*default_headers)

    def get_value(self, handler):
        value = super(Headers, self).get_value(handler)
        try:
            value.response_headers = self.response_headers.copy()
        except ValueError:
            pass
        return value

    ### request headers ###

    def __getitem__(self, request_header):
        return self.request_headers[request_header]

    def __iter__(self):
        return iter(self.request_headers)

    def __len__(self):
        return len(self.request_headers)

    def get_parsed(self, request_header, default=None):
        """Parses value and params of complex request headers.

        Args:
            request_header (str): header name.

        Kwargs:
            default: default header value.

        Returns:
            (str, dict). Header value and params dict.

        .. warning::
            Beware of using header params as kwargs since these params
            may be used for data injection into your callable entities.
            E.g. `some_function(**params)`.
        """

        try:
            raw_value = self[request_header]
        except KeyError:
            return default, {}
        parts = iter(raw_value.split(';'))
        value = next(parts)
        return value, dict(
            (lambda p, v='': (p, v.strip('"')))(*param.split('=', 1))
            for param in filter(str.strip, parts)
        )

    @cached_property
    def request_headers(self):
        return {
            name.title().replace('_', '-'): value
            for name, value in
            itertools.chain(
                (
                    self.environ.get('CONTENT_TYPE', ())
                    and
                    (('CONTENT_TYPE', self.environ['CONTENT_TYPE']), )
                ),
                (
                    self.environ.get('CONTENT_LENGTH', ())
                    and
                    (('CONTENT_LENGTH', self.environ['CONTENT_LENGTH']), )
                ),
                (
                    (name[5:], value)
                    for name, value in self.environ.items()
                    if name.startswith('HTTP_')
                )
            )
        }

    def pop(self, key, *args):
        raise NotImplementedError

    def popitem(self):
        raise NotImplementedError

    ### response headers ###

    def __delitem__(self, response_header):
        del self.response_headers[response_header.title()]

    def __setitem__(self, response_header, value):
        self.response_headers[response_header.title()] = [value]

    @cached_property
    def ready_for_response(self):
        """Returns sequence of response headers.

        Accessing first header is cause of inability to modify
        response headers after.
        """

        response_headers = self.__dict__.pop('response_headers')
        for header, values in response_headers.items():
            for value in values:
                yield header, to_bytes(value, encoding='latin1')

    @property
    def response_headers(self):
        try:
            return self.__dict__['response_headers']
        except KeyError:
            raise ValueError("Headers been already sent")

    @response_headers.setter
    def response_headers(self, value):
        self.__dict__['response_headers'] = value

    def append(self, response_header, value):
        if value is not None:
            self.response_headers[response_header.title()].append(value)

    def extend(self, *response_headers):
        for header in response_headers:
            self.append(*header)

    def setdefault(self, response_header, default=None):
        return self.response_headers.setdefault(
            response_header.title(),
            [default],
        )

    def clear(self, *response_headers):
        if response_headers:
            for response_header in response_headers:
                try:
                    del self[response_header]
                except KeyError:
                    pass
        else:
            self.response_headers.clear()
