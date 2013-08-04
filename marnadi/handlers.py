from marnadi import errors, descriptors


class HandlerProcessor(type):

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_descriptor_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_descriptor_name(attr_value, attr_name)

    def __call__(cls, environ, *args, **kwargs):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            result, result_stream = handler(*args, **kwargs), ()
            if not isinstance(result, basestring):
                try:
                    result_stream = iter(result)
                except TypeError:
                    pass
                else:
                    result = next(result_stream)
            result = str(result or '')
            if not result_stream:
                handler.headers.set('Content-Length', len(result))
            yield str(handler.status)
            for header, value in handler.headers:
                yield str(header), str(value)
            yield  # separator between headers and body
            yield result
            for chunk in result_stream:
                yield str(chunk or '')
        except errors.HttpError:
            raise
        except:
            raise errors.HttpError

    def set_descriptor_name(cls, descriptor, name):
        if isinstance(descriptor, descriptors.Descriptor):
            descriptor.name = descriptor.name or name


class Handler(object):
    # TODO implement way how to instantiate Handler (e.g. for testing purpose)

    __metaclass__ = HandlerProcessor

    SUPPORTED_HTTP_METHODS = (
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    )

    status = errors.HTTP_200_OK

    headers = descriptors.Headers()

    cookies = descriptors.Cookies()

    query = descriptors.Query()

    data = descriptors.Data(
        ('multipart/form-data', 'marnadi.mime.multipart.form_data.decode'),
        ('application/json', 'marnadi.mime.application.json.decode'),
        ('application/x-www-form-urlencoded',
            'marnadi.mime.application.x_www_form_urlencoded.decode'),
    )

    def __init__(self, environ):
        self.environ = environ

    def __call__(self, *args, **kwargs):
        request_method = self.environ.request_method
        if request_method not in self.SUPPORTED_HTTP_METHODS:
            raise errors.HttpError(
                errors.HTTP_501_NOT_IMPLEMENTED,
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        else:
            callback = getattr(self, request_method.lower(), NotImplemented)
            if callback is NotImplemented:
                raise errors.HttpError(
                    errors.HTTP_405_METHOD_NOT_ALLOWED,
                    headers=(('Allow', ', '.join(self.allowed_http_methods)), )
                )
        return callback(*args, **kwargs)

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
