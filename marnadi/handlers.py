# TODO rename module to http
import collections
import functools
import itertools
import logging

from marnadi import descriptors
from marnadi.errors import HttpError
from marnadi.helpers import Header
from marnadi.utils import to_bytes, cached_property, coroutine, metaclass

try:
    str = unicode
except NameError:
    pass


class Handler(type):

    def __new__(mcs, name, mro, attributes):
        for attribute, value in attributes.items():
            if isinstance(value, Method):
                value.name = attribute
        return super(Handler, mcs).__new__(mcs, name, mro, attributes)

    def start(cls, *args, **kwargs):
        raise NotImplementedError


class Method(object):

    __slots__ = 'name', 'func'

    class FunctionHandler(Handler):

        __function__ = NotImplemented

        __response__ = NotImplemented

        def __call__(cls, *args, **kwargs):
            return cls.__function__(*args, **kwargs)

        class classmethod(classmethod):

            def __get__(self, instance, cls):
                assert isinstance(cls, Method.FunctionHandler)
                return functools.partial(self.__func__, cls.__response__)

    def __init__(self, func=None, name=None):
        self.func = func
        self.name = name or func and func.__name__

    def __get__(self, response, response_cls):
        if response is None:
            return functools.partial(self, response_cls)
        return self.func and functools.partial(self.func, response)

    def __call__(self, response_cls, func):
        method = staticmethod(func)
        attributes = dict(
            __module__=func.__module__,
            __doc__=func.__doc__,
            __slots__=(),
        )
        response = type(func.__name__, (response_cls, ), dict(
            {self.name: method},
            **attributes
        ))
        func_replacement = self.FunctionHandler(
            func.__name__,
            (),
            dict(
                attributes,
                __function__=method,
                __response__=response,
                start=self.FunctionHandler.classmethod(response_cls.start.__func__),
            ),
        )
        return func_replacement


@metaclass(Handler)
class Response(object):

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
        except HttpError:
            raise
        except Exception as error:
            cls.logger.exception(error)
            raise

    @property
    def allowed_http_methods(self):
        for method in self.supported_http_methods:
            if getattr(self, method.lower()):
                yield method

    @Method
    def options(self, **kwargs):
        self.headers.append('Allow', ', '.join(self.allowed_http_methods))

    get = Method()

    head = Method()

    post = Method()

    put = Method()

    patch = Method()

    delete = Method()
