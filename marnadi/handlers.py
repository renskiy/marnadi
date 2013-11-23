import functools
import logging

from marnadi import errors, descriptors

logger = logging.getLogger('marnadi')


class HandlerProcessor(type):

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_descriptor_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_descriptor_name(attr_value, attr_name)

    def __call__(cls, environ, callback=None, handler_args=None, handler_kwargs=None):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            result = handler(
                callback=callback,
                handler_args=handler_args,
                handler_kwargs=handler_kwargs,
            )
            chunks, first_chunk = (), ''
            try:
                assert not isinstance(result, basestring)
                chunks = iter(result)
            except (TypeError, AssertionError):
                first_chunk = result = unicode(result or '').encode('utf-8')
            else:
                try:
                    first_chunk = unicode(next(chunks)).encode('utf-8')
                except StopIteration:
                    pass
            yield str(handler.status)
            try:
                handler.headers.set('Content-Length', len(result))
            except TypeError:
                pass
            for header in handler.headers:
                yield map(str, header)
            yield  # separator between headers and body
            yield first_chunk
            for next_chunk in chunks:
                yield unicode(next_chunk).encode('utf-8')
        except errors.HttpError:
            raise
        except Exception as error:
            logger.exception(error)
            raise errors.HttpError

    def set_descriptor_name(cls, descriptor, attr_name):
        if isinstance(descriptor, descriptors.Descriptor):
            descriptor.attr_name = attr_name


class Handler(object):

    __metaclass__ = HandlerProcessor

    SUPPORTED_HTTP_METHODS = (
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    )

    status = errors.HTTP_200_OK

    headers = descriptors.Headers(
        ('Content-Type', 'text/plain; charset=utf-8'),
    )

    cookies = descriptors.Cookies()

    query = descriptors.Query()

    data = descriptors.Data(
        ('multipart/form-data', 'marnadi.mime.multipart.form_data.Decoder'),
        ('application/json', 'marnadi.mime.application.json.Decoder'),
        ('application/x-www-form-urlencoded',
            'marnadi.mime.application.x_www_form_urlencoded.Decoder'),
    )

    def __init__(self, environ):
        self.environ = environ

    def __call__(self, callback=None, handler_args=None, handler_kwargs=None):
        request_method = self.environ.request_method
        if request_method not in self.SUPPORTED_HTTP_METHODS:
            raise errors.HttpError(
                errors.HTTP_501_NOT_IMPLEMENTED,
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        if callback is None:
            callback = getattr(self, request_method.lower(), NotImplemented)
            if callback is NotImplemented:
                raise errors.HttpError(
                    errors.HTTP_405_METHOD_NOT_ALLOWED,
                    headers=(('Allow', ', '.join(self.allowed_http_methods)), )
                )
        return callback(*handler_args or (), **handler_kwargs or {})

    @property
    def allowed_http_methods(self):
        for method in self.SUPPORTED_HTTP_METHODS:
            allowed_method = getattr(self, method.lower(), NotImplemented)
            if allowed_method is NotImplemented:
                continue
            yield method

    def options(self, *args, **kwargs):
        self.headers.set('Allow', ', '.join(self.allowed_http_methods))

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented


def handler(callback):

    def _decorator(func):

        @functools.wraps(func)
        def _func(environ, handler_args=None, handler_kwargs=None):
            return callback(
                environ,
                callback=func,
                handler_args=handler_args,
                handler_kwargs=handler_kwargs,
            )

        return _func

    try:
        if issubclass(callback, Handler):
            return _decorator
    except TypeError:
        pass

    func, callback = callback, Handler
    return _decorator(func)
