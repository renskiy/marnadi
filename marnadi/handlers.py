# TODO rename module to http
import collections
import functools
import itertools
import logging

from marnadi import descriptors
from marnadi.errors import HttpError
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

            def __get__(self, instance, instance_class):
                assert isinstance(instance_class, Method.FunctionHandler)
                return functools.partial(
                    self.__func__, instance_class.__response__)

    def __init__(self, func=None, name=None):
        self.func = func
        self.name = name or func and func.__name__

    def __get__(self, response, response_class):
        if response is None:
            return functools.partial(self, response_class)
        return self.func and functools.partial(self.func, response)

    def __call__(self, response_class, callback):
        method = staticmethod(callback)
        if isinstance(callback, self.FunctionHandler):
            setattr(callback.__response__, self.name, method)
            return callback
        attributes = dict(
            __module__=callback.__module__,
            __doc__=callback.__doc__,
            __slots__=(),
        )
        response = type(callback.__name__, (response_class, ), dict(
            {self.name: method},
            **attributes
        ))
        callback_replacement = self.FunctionHandler(
            callback.__name__,
            (),
            dict(
                attributes,
                __function__=method,
                __response__=response,
                start=self.FunctionHandler.classmethod(
                    response_class.start.__func__),
            ),
        )
        return callback_replacement


@metaclass(Handler)
class Response(object):

    logger = logging.getLogger('marnadi')

    status = '200 OK'

    supported_http_methods = {
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    }

    if hasattr(collections.Iterator, '__slots__'):
        __slots__ = 'app', 'request', '__weakref__'

    headers = descriptors.Headers()

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
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = Method()

    head = Method()

    post = Method()

    put = Method()

    patch = Method()

    delete = Method()
