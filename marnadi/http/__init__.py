import functools

from .cookies import Cookies
from .headers import Headers, Header
from .error import Error
from .data import Data


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
