from marnadi import byte_str

HTTP_200_OK = '200 OK'

HTTP_400_BAD_REQUEST = '400 Bad Request'
HTTP_401_UNAUTHORIZED = '401 Unauthorized'
HTTP_403_FORBIDDEN = '403 Forbidden'
HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'
HTTP_411_LENGTH_REQUIRED = '411 Length Required'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'
HTTP_501_NOT_IMPLEMENTED = '501 Not Implemented'


class HttpError(Exception):

    default_headers = ()

    def __init__(self, status=HTTP_500_INTERNAL_SERVER_ERROR,
                 data=None, headers=None):
        self._status = status
        self._headers = headers or ()
        self._data = data

    def __len__(self):
        return 1

    def __iter__(self):
        yield self.__str__()

    def __str__(self):
        return byte_str(self._data)

    def __repr__(self):
        return '%s: %s' % (self.status, self)

    @property
    def status(self):
        return byte_str(self._status)

    @property
    def headers(self):
        headers_sent = set()
        for header, value in self._headers:
            header, value = byte_str(header), byte_str(value)
            headers_sent.add(header)
            yield header, value
        for header, value in self.default_headers:
            header = header
            if header not in headers_sent:
                yield header, value
