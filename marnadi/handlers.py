import logging
import types

from marnadi import descriptors, Header
from marnadi.errors import HttpError
from marnadi.utils import metaclass, to_bytes


class Handler(type):

    __func__ = None

    def __call__(cls, *args, **kwargs):
        func = cls.__func__
        if func is not None:
            return func(*args, **kwargs)
        return super(Handler, cls).__call__(*args, **kwargs)

    def get_instance(cls, *args, **kwargs):
        return type.__call__(cls, *args, **kwargs)

    def provider(cls, func):
        assert callable(func)
        attributes = dict(
            __func__=staticmethod(func),
            __module__=func.__module__,
            __doc__=func.__doc__,
        )
        return type(cls)(func.__name__, (cls, ), attributes)

    def start(cls, **kwargs):
        raise NotImplementedError


@metaclass(Handler)
class Response(object):

    __slots__ = 'request', '__weakref__'

    logger = logging.getLogger('marnadi')

    supported_http_methods = {
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    }

    status = '200 OK'

    headers = descriptors.Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    cookies = descriptors.Cookies()

    def __init__(self, request):
        self.request = request

    def __call__(self, **kwargs):
        if self.request.method not in self.supported_http_methods:
            raise HttpError(
                '501 Not Implemented',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(self, self.request.method.lower()) or self.__func__
        if callback is None:
            raise HttpError(
                '405 Method Not Allowed',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(**kwargs)

    @classmethod
    def start(cls, **kwargs):
        """Start response with given params.

        Note:
            Error responses can be customized by overriding this method.
            For example your version may catch `HttpError` from original
            implementation and reraise it with necessary content data
            (which may be a HTML containing formatted stack trace).
        """
        request, start_response = yield
        try:
            response = cls.get_instance(request)
            result = response(**kwargs)
            if isinstance(result, types.GeneratorType):
                body = (
                    to_bytes(chunk, error_callback=cls.logger.exception)
                    for chunk in result
                )
            else:
                body = (to_bytes(result), )
                response.headers.setdefault('Content-Length', len(body[0]))
            start_response(
                response.status,
                list(response.headers.items(stringify=True)),
            )
            yield body
        except HttpError:
            raise
        except Exception as error:
            cls.logger.exception(error)
            raise HttpError

    @property
    def allowed_http_methods(self):
        func = self.__func__
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
