HTTP_200_OK = '200 OK'

HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'
HTTP_501_NOT_IMPLEMENTED = '501 Not Implemented'


class HttpError(Exception):

    default_headers = ()

    def __init__(self, status=HTTP_500_INTERNAL_SERVER_ERROR,
                 data=None, headers=None):
        self.status = status
        self._headers = headers or ()
        self._data = data
        self._prepared_data = None

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return self.data

    @property
    def headers(self):
        headers_sent = set()
        for header, value in self._headers:
            header, value = str(header).title(), str(value)
            headers_sent.add(header)
            yield header, value
        for header, value in self.default_headers:
            header = header.title()
            if header not in headers_sent:
                yield header, value

    @property
    def data(self):
        if self._prepared_data is None:
            self._prepared_data = self.prepare_data(self._data)
        return self._prepared_data

    def prepare_data(self, data):
        return data and str(data) or ''