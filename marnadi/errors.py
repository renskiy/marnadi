import collections

from marnadi import Header, descriptors
from marnadi.utils import to_bytes


class HttpError(Exception, collections.Iterable, collections.Sized):

    __slots__ = 'status', 'data', '__weakref__'

    headers = descriptors.Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(
        self,
        status='500 Internal Server Error',
        data=None,
        headers=None,
        error=None,
    ):
        self.status = status
        self.data = data or status
        if headers:
            self.headers.extend(*headers)

    def __len__(self):
        return 1

    def __iter__(self):
        yield to_bytes(self.data)
