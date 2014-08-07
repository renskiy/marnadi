import abc
import logging
import types

from marnadi import descriptors, Header
from marnadi.errors import HttpError
from marnadi.utils import metaclass, to_bytes


@metaclass(abc.ABCMeta)
class Handler(object):

    __slots__ = 'request', '__weakref__'

    logger = logging.getLogger('marnadi')

    supported_http_methods = (
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    )

    status = '200 OK'

    headers = descriptors.Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    cookies = descriptors.Cookies()

    def __new__(cls, *args, **kwargs):
        if cls.func is not None:
            return cls.func(*args, **kwargs)
        return super(Handler, cls).__new__(cls)

    def __init__(self, request):
        self.request = request

    def get_result(self, *method_args, **method_kwargs):
        if self.request.method not in self.supported_http_methods:
            raise HttpError(
                '501 Not Implemented',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(self, self.request.method.lower(), NotImplemented)
        if callback is NotImplemented:
            raise HttpError(
                '405 Method Not Allowed',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(*method_args, **method_kwargs)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls.func is None:
            return cls(*args, **kwargs)
        return type(
            cls.__name__,
            (cls, ),
            dict(__new__=super(Handler, cls).__new__),
        )(*args, **kwargs)

    @classmethod
    def handle(cls, *args, **kwargs):
        request, start_response = yield
        try:
            response = cls.get_instance(request)
            result = response.get_result(*args, **kwargs)
            if isinstance(result, types.GeneratorType):
                body = (
                    to_bytes(chunk, error_callback=cls.logger.exception)
                    for chunk in result
                )
            else:
                body = to_bytes(result),
                response.headers.setdefault('Content-Length', len(body[0]))
            status = response.status
            headers = [
                (header, to_bytes(value, encoding='latin1'))
                for header, value in response.headers.items()
            ]
            start_response(status, headers)
            yield body
        except HttpError:
            raise
        except Exception as error:
            cls.logger.exception(error)
            raise HttpError(exception=error)

    @property
    def allowed_http_methods(self):
        for method in self.supported_http_methods:
            if getattr(self, method.lower(), NotImplemented) is NotImplemented:
                continue
            yield method

    @classmethod
    def decorator(cls, func):
        method = staticmethod(func)
        attributes = dict(
            func=method,
            __module__=func.__module__,
            __doc__=func.__doc__,
        )
        for supported_method in cls.supported_http_methods:
            supported_method = supported_method.lower()
            if getattr(cls, supported_method, NotImplemented) is NotImplemented:
                attributes[supported_method] = method
        return type(cls)(func.__name__, (cls, ), attributes)

    def options(self, *args, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented

    func = None  # function decorated by `cls.decorator`
