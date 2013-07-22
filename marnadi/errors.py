HTTP_200_OK = '200 OK'

HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'
HTTP_501_NOT_IMPLEMENTED = '501 Not Implemented'


class HttpError(Exception):

    @property
    def headers(self):
        default_headers = {
            'Content-Type': 'text/plain',
            'Content-Length': None,
        }
        for header, value in self._headers:
            header, value = str(header).title(), str(value)
            if header in default_headers:
                default_headers[header] = value
            else:
                yield (header, value)
        if default_headers['Content-Length'] is None:
            default_headers['Content-Length'] = len(self.data)
        for header in default_headers.iteritems():
            yield header

    def __init__(self, status=HTTP_500_INTERNAL_SERVER_ERROR,
                 data=None, headers=None):
        self.status = status
        self._headers = headers or ()
        self.data = data or status

    def __iter__(self):
        yield self.data