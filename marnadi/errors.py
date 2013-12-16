import collections
import itertools

from marnadi.descriptors.headers import Header

HTTP_200_OK = '200 OK'
HTTP_204_NO_CONTENT = '204 No Content'

HTTP_400_BAD_REQUEST = '400 Bad Request'
HTTP_401_UNAUTHORIZED = '401 Unauthorized'
HTTP_403_FORBIDDEN = '403 Forbidden'
HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'
HTTP_411_LENGTH_REQUIRED = '411 Length Required'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'
HTTP_501_NOT_IMPLEMENTED = '501 Not Implemented'


class HttpError(Exception):

    default_headers = (
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(self, status=HTTP_500_INTERNAL_SERVER_ERROR,
                 data=None, headers=(), info=None):
        self.status = str(status)
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
