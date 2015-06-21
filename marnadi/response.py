import collections
import itertools
import logging

from marnadi import http
from marnadi.utils import to_bytes, cached_property, coroutine, metaclass

try:
    str = unicode
except NameError:
    pass


@metaclass(http.Handler)
class Response(object):

    logger = logging.getLogger('marnadi')

    status = '200 OK'

    supported_http_methods = {
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    }

    if hasattr(collections.Iterator, '__slots__'):
        __slots__ = 'app', 'request', '__weakref__'

    headers = http.Headers(
        ('Content-Type', http.Header('text/plain', charset='utf-8')),
    )

    cookies = http.Cookies()

    def __init__(self, app, request):
        self.app = app
        self.request = request

    def __call__(self, **kwargs):
        if self.request.method not in self.supported_http_methods:
            raise http.Error(
                '501 Not Implemented',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(self, self.request.method.lower())
        if callback is None:
            raise http.Error(
                '405 Method Not Allowed',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(**kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)

    def next(self):
        return self.__next__()

    @cached_property
    @coroutine
    def iterator(self):
        result = yield
        if result is None or isinstance(result, (str, bytes)):
            chunk = to_bytes(result)
            self.headers['Content-Length'] = len(chunk)
            yield chunk
        else:
            chunks = iter(result)
            first_chunk = to_bytes(next(chunks, b''))
            try:
                result_length = len(result)
            except TypeError:  # result doesn't support len()
                pass
            else:
                if result_length <= 1:
                    self.headers['Content-Length'] = len(first_chunk)
            yield first_chunk
            for chunk in chunks:
                yield to_bytes(chunk, error_callback=self.logger.exception)

    @classmethod
    def start(cls, *args, **params):
        try:
            response = cls(*args)
            result = response(**params)
            response.iterator = itertools.chain(
                (response.iterator.send(result), ),
                response.iterator
            )
            return response
        except http.Error:
            raise
        except Exception as error:
            cls.logger.exception(error)
            raise

    @property
    def allowed_http_methods(self):
        for method in self.supported_http_methods:
            if getattr(self, method.lower()):
                yield method

    @http.Method
    def options(self, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = http.Method()

    head = http.Method()

    post = http.Method()

    put = http.Method()

    patch = http.Method()

    delete = http.Method()
