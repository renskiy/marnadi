import collections
import functools

from marnadi.http.data import Data
from marnadi.http.cookies import Cookies
from marnadi.http.headers import Headers


class Header(collections.Mapping):

    __slots__ = 'value', 'params'

    def __init__(self, *value, **params):
        assert len(value) == 1
        self.value = value[0]
        self.params = params

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __str__(self):
        return self.stringify()

    def __bytes__(self):
        value = self.stringify()
        if isinstance(value, bytes):  # python 2.x
            return value
        return value.encode(encoding='latin1')

    def __getitem__(self, item):
        return self.params[item]

    def __iter__(self):
        return iter(self.params)

    def __len__(self):
        len(self.params)

    def stringify(self):
        if not self.params:
            return str(self.value)
        return '{value}; {params}'.format(
            value=self.value,
            params='; '.join(
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in self.params.items()
            ),
        )


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
