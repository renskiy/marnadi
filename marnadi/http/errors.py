from marnadi.http import managers

HTTP_200_OK = '200 OK'

HTTP_404_NOT_FOUND = '404 Not Found'
HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'

HTTP_500_INTERNAL_SERVER_ERROR = '500 Internal Server Error'
HTTP_501_NOT_IMPLEMENTED = '501 Not Implemented'


class HttpError(Exception):

    status = HTTP_500_INTERNAL_SERVER_ERROR

    headers = managers.Headers(
        ('Content-Type', 'text/plain')
    )

    def __init__(self, status=None):
        self.status = status or self.status

    @property
    def body(self):
        yield self.status

    def __iter__(self):
        return iter(self.body)