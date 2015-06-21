from marnadi.http import Header, Headers
from marnadi.utils import to_bytes


class Error(Exception):

    __slots__ = 'status', 'data', '__weakref__'

    headers = Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(
        self,
        status='500 Internal Server Error',
        data=None,
        headers=(),
    ):
        self.status = status
        self.data = to_bytes(data or status)
        self.update_headers(headers)

    def __len__(self):
        return 1

    def __iter__(self):
        yield to_bytes(self.data)

    def update_headers(self, headers):
        self.headers.extend(headers)
        self.headers['Content-Length'] = len(self.data)
