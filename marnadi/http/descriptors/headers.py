import collections

from marnadi.http.descriptors import Descriptor


class Headers(Descriptor):
    """Request/response headers manager.

    Note that request handler iterates over the response headers when it's
    ready to generate the response, after that there is no more ability to
    modify list of response headers. So be sure you set all necessary headers
    before you going to iterate over the response headers for some reason.
    """

    def __init__(self, *response_headers, **kwargs):
        super(Headers, self).__init__(**kwargs)
        self._headers_sent = False
        self._response_headers = collections.defaultdict(list)
        for header, value in response_headers or ():
            self.add(header, value)

    ### request headers ###

    def __getitem__(self, request_header):
        result = self.get(request_header)
        if result is None:
            raise KeyError
        return result

    def get(self, request_header, default=None):
        getattr(self.environ, 'http_%s' % request_header.lower(), default)

    ### response headers ###

    def __iter__(self):
        self._next = (
            (header, value)
            for header, values in self._response_headers.viewitems()
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

    def add(self, response_header, value):
        self.response_headers[response_header].append(value)

    def extend(self, response_headers):
        for response_header, value in response_headers:
            self.add(response_header, value)

    def update(self, response_headers):
        replaced_headers = []
        for response_header, value in response_headers:
            if response_header not in replaced_headers:
                self.remove(response_header)
                replaced_headers.append(response_header)
            self.add(response_header, value)

    def set(self, response_header, value):
        self.response_headers[response_header] = [value]

    def remove(self, response_header):
        del self.response_headers[response_header]
