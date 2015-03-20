import logging
import itertools

from marnadi import descriptors, Header
from marnadi.errors import HttpError
from marnadi.utils import metaclass, to_bytes, cached_property, coroutine

try:
    str = unicode
except NameError:
    pass


class Handler(type):

    __func__ = None

    logger = logging.getLogger('marnadi')

    def __call__(cls, *args, **kwargs):
        func = cls.__func__
        if func is not None:
            return func(*args, **kwargs)
        return super(Handler, cls).__call__(*args, **kwargs)

    def provider(cls, func):
        assert callable(func)
        attributes = dict(
            __func__=staticmethod(func),
            __module__=func.__module__,
            __doc__=func.__doc__,
            __slots__=(),
        )
        return type(cls)(func.__name__, (cls, ), attributes)

    @coroutine
    def prepare(cls, **kwargs):
        """Initializes response generator with given params.

        Note:
            Error responses can be customized by overriding this method.
            For example your version may catch `HttpError` from original
            implementation and re-raise it with necessary content data
            (which may be a HTML containing formatted traceback).
        """
        app, request = yield
        try:
            response = type.__call__(cls, app, request)  # response instance
            response.start(**kwargs)
            yield response
        except HttpError:
            raise
        except Exception as error:
            cls.logger.exception(error)
            raise HttpError(error=error)


@metaclass(Handler)
class Response(object):

    __slots__ = 'app', 'request', '__weakref__'

    supported_http_methods = {
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    }

    status = '200 OK'

    headers = descriptors.Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    cookies = descriptors.Cookies()

    def __init__(self, app, request):
        self.app = app
        self.request = request

    def __call__(self, **kwargs):
        if self.request.method not in self.supported_http_methods:
            raise HttpError(
                '501 Not Implemented',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(
            self,
            self.request.method.lower()
        ) or self.__class__.__func__
        if callback is None:
            raise HttpError(
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

    def start(self, **kwargs):
        result = self.__call__(**kwargs)
        self.iterator = itertools.chain(
            (self.iterator.send(result), ),
            self.iterator
        )

    @cached_property
    @coroutine
    def iterator(self):
        result = yield
        if result is None or isinstance(result, (str, bytes)):
            chunk = to_bytes(result)
            self.headers.setdefault('Content-Length', len(chunk))
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
                    self.headers.setdefault(
                        'Content-Length',
                        len(first_chunk),
                    )
            for chunk in itertools.chain((first_chunk, ), chunks):
                yield to_bytes(chunk, error_callback=self.logger.exception)

    @property
    def allowed_http_methods(self):
        func = self.__class__.__func__
        for method in self.supported_http_methods:
            if func or getattr(self, method.lower()):
                yield method

    def options(self, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = None

    head = None

    post = None

    put = None

    patch = None

    delete = None
