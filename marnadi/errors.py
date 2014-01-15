import collections
import itertools

from marnadi import Header


class HttpError(Exception):

    default_headers = (
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(self, status='500 Internal Server Error',
                 data=None, headers=(), exception=None):
        self.status = status
        self._headers = headers
        self._data = data
        self.exception = exception

    def __len__(self):
        return 1

    def __iter__(self):
        if self._data is None:
            yield ''
        elif isinstance(self._data, unicode):
            yield self._data.encode('utf-8')
        else:
            yield str(self._data)

    def __str__(self):
        return "%s, exception: %s" % (self.status, self.exception)

    @property
    def headers(self):
        headers = collections.defaultdict(list)
        default_headers = collections.defaultdict(list)
        for header, value in self._headers:
            headers[header.title()].append(value)
        for header, value in self.default_headers:
            header = header.title()
            if header not in headers:
                default_headers[header].append(value)
        return [
            (header, str(value))
            for header, values in itertools.chain(
                headers.iteritems(),
                default_headers.iteritems(),
            )
            for value in values
        ]
