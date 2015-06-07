import collections
import functools
import itertools
import logging

from marnadi import descriptors, Header
from marnadi.errors import HttpError
from marnadi.utils import to_bytes, cached_property, coroutine

try:
    str = unicode
except NameError:
    pass


class Response(collections.Iterator):

    logger = logging.getLogger('marnadi')

    status = '200 OK'

    supported_http_methods = {
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    }

    if hasattr(collections.Iterator, '__slots__'):
        __slots__ = 'app', 'request', '__weakref__'

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
        callback = getattr(self, self.request.method.lower())
        if callback is None:
            raise HttpError(
                '405 Method Not Allowed',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(**kwargs)

    @classmethod
    def __subclasshook__(cls, subclass):
        return isinstance(subclass, cls.FunctionHandler) or NotImplemented

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
            yield first_chunk
            for chunk in chunks:
                yield to_bytes(chunk, error_callback=self.logger.exception)

    class FunctionHandler(type):

        __function__ = NotImplemented

        __response__ = NotImplemented

        def __call__(cls, *args, **kwargs):
            return cls.__function__(*args, **kwargs)

        def prepare(cls, **kwargs):
            raise NotImplementedError

        def get_instance(cls, *args, **kwargs):
            raise NotImplementedError

        class classmethod(classmethod):

            def __get__(self, instance, cls):
                assert isinstance(cls, Response.FunctionHandler)
                return functools.partial(self.__func__, cls.__response__)

    @classmethod
    def handler(cls, *methods):
        def decorator(func):
            method = staticmethod(func)
            attributes = dict(
                __module__=func.__module__,
                __doc__=func.__doc__,
                __slots__=(),
            )
            response_class = type(func.__name__, (cls, ), dict(
                {m.lower(): method for m in methods},
                **attributes
            ))
            func_replacement = cls.FunctionHandler(
                func.__name__,
                (),
                dict(
                    attributes,
                    __function__=method,
                    __response__=response_class,
                    prepare=classmethod(cls.prepare.__func__),
                    get_instance=cls.FunctionHandler.classmethod(
                        cls.get_instance.__func__),
                ),
            )
            return func_replacement
        return decorator

    def start(self, **kwargs):
        try:
            result = self(**kwargs)
            self.iterator = itertools.chain(
                (self.iterator.send(result), ),
                self.iterator
            )
        except HttpError:
            raise
        except Exception as error:
            self.logger.exception(error)
            raise
        return self

    @classmethod
    @coroutine
    def prepare(cls, **kwargs):
        app, request = yield
        yield cls.get_instance(app, request).start(**kwargs)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @property
    def allowed_http_methods(self):
        for method in self.supported_http_methods:
            if getattr(self, method.lower()):
                yield method

    def options(self, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = None

    head = None

    post = None

    put = None

    patch = None

    delete = None
