import collections
import copy

from marnadi.descriptors import Descriptor


class Headers(Descriptor):
    """Request/response headers.

    Request headers can be accessed ONLY by key or `get` method. All other
    ways lead to response headers.

    Note:
        Request handler uses iteration over the response headers when
        it's ready to generate response, so there is no more ability to modify
        response headers once iteration has been started.
    """

    def __init__(self, *response_headers, **kwargs):
        super(Headers, self).__init__(**kwargs)
        self._headers_sent = False
        self._response_headers = collections.defaultdict(list)
        self.extend(*response_headers)

    def clone(self, owner_instance):
        instance = super(Headers, self).clone(owner_instance)
        instance._headers_sent = False
        instance._response_headers = copy.copy(self._response_headers)
        return instance

    ### request headers ###

    def __getitem__(self, request_header):
        result = self.get(request_header)
        if result is None:
            raise KeyError
        return result

    def __delitem__(self, *args, **kwargs):
        raise TypeError("Request headers are read only, "
                        "use clear() if you wish delete response header")

    def __setitem__(self, *args, **kwargs):
        raise TypeError("Request headers are read only, use set() or append() "
                        "if you wish set or append new response header")

    def get(self, request_header, default=None):
        return getattr(
            self.environ,
            'http_%s' % request_header.lower().replace('-', '_'),
            default
        )

    def get_splitted(self, request_header):
        """Returns value and params of complex request header"""

        raw_value = self.get(request_header, default='')
        parts = iter(raw_value.split(';'))
        value = parts.next()
        return value, dict(
            (key, value.strip('"'))
            for param in parts
            for key, value in param.strip().split('=', 1)
        )

    ### response headers ###

    def __iter__(self):
        self._next = (
            (header, value)
            for header, values in self._response_headers.iteritems()
            for value in values
        ).next
        return self

    def next(self):
        self._headers_sent = True
        return self._next()

    @property
    def response_headers(self):
        assert not self._headers_sent, "headers been already sent"
        return self._response_headers

    def append(self, response_header, value):
        self.response_headers[response_header.title()].append(value)

    def extend(self, *response_headers):
        for header in response_headers:
            self.append(*header)

    def set(self, response_header, value):
        self.response_headers[response_header.title()] = [value]

    def clear(self, *response_headers):
        if response_headers:
            for response_header in response_headers:
                del self.response_headers[response_header.title()]
        else:
            self.response_headers.clear()