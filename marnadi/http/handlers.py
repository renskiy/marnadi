from marnadi.http import errors, managers


class HandlerProcessor(type):

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.update_manager_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.update_manager_name(attr_value, attr_name)

    def __call__(cls, environ, *args, **kwargs):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            request_method = environ.request_method
            try:
                assert request_method in handler.SUPPORTED_HTTP_METHODS
            except AssertionError:
                handler.status = errors.HTTP_501_NOT_IMPLEMENTED
                method = handler.http_options
            else:
                handler_method_name = 'http_%s' % request_method.lower()
                method = getattr(handler, handler_method_name)
            result = method(*args, **kwargs)
            result_iterator = ()
            if not isinstance(result, basestring):
                try:
                    result_iterator = iter(result)
                except TypeError:
                    # assume result is an object with a string representation
                    pass
                else:
                    result = next(result_iterator)
            result = str(handler.transform_result(result) or '')
            if not result_iterator:
                handler.headers.set('Content-Length', len(result))
            yield str(handler.status)
            for header, value in handler.headers:
                yield str(header), str(value)
            yield  # separator between headers and body
            yield result
            for chunk in result_iterator:
                yield str(handler.transform_chunk(chunk) or '')
        except errors.HttpError:
            raise
        except:
            raise errors.HttpError

    def update_manager_name(cls, manager, name):
        if isinstance(manager, managers.Manager):
            manager.name = manager.name or name


class Handler(object):
    # TODO implement way how to instantiate Handler (e.g. for testing purpose)

    __metaclass__ = HandlerProcessor

    SUPPORTED_HTTP_METHODS = (
        'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE',
    )

    @property
    def ALLOWED_HTTP_METHODS(self):
        for method in self.SUPPORTED_HTTP_METHODS:
            allowed_method = getattr(self, method.lower(), None)
            if callable(allowed_method):
                yield method

    status = errors.HTTP_200_OK

    headers = managers.Headers()

    cookies = managers.Cookies()

    def __init__(self, environ):
        self.environ = environ

    def __getattribute__(self, name):
        attr = super(Handler, self).__getattribute__(name)
        if (
            attr is NotImplemented
                and
            attr.upper() in self.SUPPORTED_HTTP_METHODS
        ):
            self.status = errors.HTTP_405_METHOD_NOT_ALLOWED
            return self.options
        return attr

    def transform_result(self, result):
        """Transforms result before sending it to the response stream.

        If result splitted to chunks then only first chunk will be transformed
        by this method, all others will be proceeded by `transform_chunk`.

        Unlike to `transform_chunk` this method still allows headers modifying.
        """

        return self.transform_chunk(result)

    def transform_chunk(self, chunk):
        """Transforms result chunk before sending it to the response stream.

        First chunk is transformed by `transform_result`.

        This method doesn't allow headers modifying due to fact that they were
        already sent.
        """

        return chunk

    def http_options(self, *args, **kwargs):
        self.headers.set('Allow', ', '.join(self.ALLOWED_HTTP_METHODS))

    http_get = NotImplemented

    http_head = NotImplemented

    http_post = NotImplemented

    http_put = NotImplemented

    http_patch = NotImplemented

    http_delete = NotImplemented
