import collections
import itertools

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

    def __init__(self, *default_headers):
        super(Headers, self).__init__()
        self._headers_sent = False
        self._request_headers = None
        self._response_headers = collections.defaultdict(list)
        self.extend(*default_headers)

    def __copy__(self):
        value = self.__class__()
        value._response_headers = self._response_headers.copy()
        return value

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

    def __str__(self):
        return str(self.request_headers)

    def get(self, request_header, *args, **kwargs):
        return self.request_headers.get(request_header.title(), *args, **kwargs)

    def get_parsed(self, request_header):
        """Returns value and params of complex request header"""

        raw_value = self.get(request_header, '')
        parts = iter(raw_value.split(';'))
        value = parts.next()
        return value, dict(
            (lambda p, v='': (p, v.strip('"')))(*param.split('=', 1))
            for param in (part.strip() for part in parts) if param
        )

    @property
    def request_headers(self):
        if self._request_headers is None:
            self._request_headers = dict(
                (name.title().replace('_', '-'), value)
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
                        for name, value in self.environ.iteritems()
                        if name.startswith('HTTP_')
                    )
                )
            )
        return self._request_headers

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

    def append(self, response_header, value, **attributes):
        value = self.make_header_value(value, **attributes)
        self.response_headers[response_header.title()].append(value)

    def extend(self, *response_headers):
        for header in response_headers:
            self.append(*header)

    def set(self, response_header, value, **attributes):
        value = self.make_header_value(value, **attributes)
        self.response_headers[response_header.title()] = [value]

    def set_if_not(self, response_header, value, **attributes):
        response_header = response_header.title()
        if response_header in self.response_headers:
            return
        self.set(response_header, value, **attributes)

    def clear(self, *response_headers):
        if response_headers:
            for response_header in response_headers:
                del self.response_headers[response_header.title()]
        else:
            self.response_headers.clear()

    ### helpers ###

    def make_header_value(self, value, **attributes):
        if not attributes:
            return value
        return "%s; %s" % (
            value, '; '.join(
                attr_name + ('' if attr_value is None else '=%s' % attr_value)
                for attr_name, attr_value in attributes.iteritems()
            )
        )