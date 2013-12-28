import functools
import logging

from marnadi import descriptors, Header
from marnadi.errors import HttpError


class HandlerType(type):

    logger = logging.getLogger('marnadi')

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerType, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_descriptor_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerType, cls).__setattr__(attr_name, attr_value)
        cls.set_descriptor_name(attr_value, attr_name)

    def __call__(cls, *args, **kwargs):
        if cls.func is not None:
            return cls.func(*args, **kwargs)
        return super(HandlerType, cls).__call__(*args, **kwargs)

    def decorator(cls, func):
        method = staticmethod(func)
        attributes = dict(func=method)
        for supported_method in cls.SUPPORTED_HTTP_METHODS:
            supported_method = supported_method.lower()
            if getattr(cls, supported_method, NotImplemented) is NotImplemented:
                attributes[supported_method] = method
        return functools.update_wrapper(
            type('', (cls, ), attributes),
            func, updated=(),
        )

    def handle(cls, environ, args=(), kwargs=None):
        try:
            handler = super(HandlerType, cls).__call__(environ)
            result = handler(*args, **kwargs or {})
            chunks, first_chunk = (), ''
            try:
                if not isinstance(result, basestring):
                    chunks = iter(result)
                try:
                    first_chunk = unicode(next(chunks) or '').encode('utf-8')
                except StopIteration:
                    pass
            except TypeError:
                first_chunk = unicode(result or '').encode('utf-8')
            if not handler.headers.setdefault('Content-Length'):
                try:
                    if not chunks or len(result) == 1:
                        handler.headers['Content-Length'] = len(first_chunk)
                except TypeError:
                    pass
            yield handler.status
            for header, value in handler.headers.flush():
                yield header, str(value)
            yield  # separator between headers and body
            yield first_chunk
            for next_chunk in chunks:
                next_chunk = unicode(next_chunk or '').encode('utf-8')
                yield next_chunk
        except HttpError:
            raise
        except Exception as error:
            cls.logger.exception(error)
            cls.handle_exception(error, environ, args, kwargs)

    def handle_exception(cls, error, environ, args, kwargs):
        raise HttpError(exception=error)

    @staticmethod
    def set_descriptor_name(descriptor, attr_name):
        if isinstance(descriptor, descriptors.Descriptor):
            descriptor.attr_name = attr_name


class Handler(object):

    __metaclass__ = HandlerType

    SUPPORTED_HTTP_METHODS = (
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    )

    status = '200 OK'

    headers = descriptors.Headers(
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    cookies = descriptors.Cookies()

    query = descriptors.Query()

    data = descriptors.Data(
        ('application/json', 'marnadi.mime.application.json.Decoder'),
        ('application/x-www-form-urlencoded',
            'marnadi.mime.application.x_www_form_urlencoded.Decoder'),
    )

    func = None  # function decorated by this class

    def __init__(self, environ):
        self.environ = environ

    def __call__(self, *args, **kwargs):
        request_method = self.environ.request_method
        if request_method not in self.SUPPORTED_HTTP_METHODS:
            raise HttpError(
                '501 Not Implemented',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(self, request_method.lower(), NotImplemented)
        if callback is NotImplemented:
            raise HttpError(
                '405 Method Not Allowed',
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(*args, **kwargs)

    @property
    def allowed_http_methods(self):
        for method in self.SUPPORTED_HTTP_METHODS:
            if getattr(self, method.lower(), NotImplemented) is NotImplemented:
                continue
            yield method

    def options(self, *args, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)
        return self.__doc__

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented