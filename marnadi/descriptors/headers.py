import collections
import itertools
import UserDict

from marnadi.descriptors import Descriptor


class Header(object):

    def __init__(self, value, **attributes):
        self.value = value
        self.attributes = attributes

    def __str__(self):
        return self.make_value(self.value, **self.attributes)

    @staticmethod
    def make_value(value, **attributes):
        if not attributes:
            return value
        return "%s; %s" % (
            value, '; '.join(
                attr_name + ('' if attr_value is None else '=%s' % attr_value)
                for attr_name, attr_value in attributes.iteritems()
            )
        )


class Headers(Descriptor, UserDict.DictMixin):
    """Headers - dict-like object which allow to read request
    and set response headers.

    All methods are divided into two groups: getters and setters where
    getters usually provide access to request headers and setters
    allow to modify response headers. For more information see
    particular method description.
    """

    def __init__(self, *default_headers):
        super(Headers, self).__init__()
        self._next = None
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
        return self.request_headers[request_header]

    def iterkeys(self):
        return self.request_headers.iterkeys()

    def iteritems(self):
        return self.request_headers.iteritems()

    def keys(self):
        return self.request_headers.keys()

    def get_parsed(self, request_header, default=None):
        """Returns value and params of complex request header"""

        try:
            unparsed_value = self[request_header]
        except KeyError:
            return default, {}
        parts = iter(unparsed_value.split(';'))
        value = parts.next()
        return value, dict(
            (lambda p, v='': (p, v.strip('"')))(*param.split('=', 1))
            for param in itertools.ifilter(str.strip, parts)
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

    def pop(self, key, *args):
        raise NotImplementedError("`Headers.pop()` is not implemented")

    def popitem(self):
        raise NotImplementedError("`Headers.popitem()` is not implemented")

    ### response headers ###

    def __delitem__(self, response_header):
        self.clear(response_header)

    def __setitem__(self, response_header, value):
        self.set(response_header, value)

    def for_send(self):
        for header, values in self.response_headers.iteritems():
            self._headers_sent = True
            for value in values:
                yield header, value

    @property
    def response_headers(self):
        assert not self._headers_sent, "Headers been already sent"
        return self._response_headers

    def append(self, response_header, value):
        self.response_headers[response_header.title()].append(value)

    def extend(self, *response_headers):
        for header in response_headers:
            self.append(*header)

    def set(self, response_header, value):
        self.response_headers[response_header.title()] = [value]

    def setdefault(self, response_header, default=None):
        try:
            return self.response_headers[response_header.title()]
        except KeyError:
            self.set(response_header, default)
        return default

    def clear(self, *response_headers):
        if response_headers:
            for response_header in response_headers:
                del self.response_headers[response_header.title()]
        else:
            self.response_headers.clear()
