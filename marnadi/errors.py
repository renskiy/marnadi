import collections
import itertools

from marnadi import Header


class HttpError(Exception):

    default_headers = (
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(self, status='500 Internal Server Error',
                 data=None, headers=(), info=None):
        self.status = status
        self._headers = headers
        self._data = data
        self.info = info

    def __len__(self):
        return 1

    def __iter__(self):
        yield unicode(self._data or '').encode('utf-8')

    def __str__(self):
        return "%s, info: %s" % (self.status, self.info)

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
