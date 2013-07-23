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
            result_flow = handler(*args, **kwargs)
            first_chunk = next(result_flow)
            yield str(handler.status)
            for header, value in handler.headers:
                yield str(header), str(value)
            yield  # separator between headers and body
            yield first_chunk
            for chunk in result_flow:
                yield chunk
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

    @property
    def ALLOWED_HTTP_METHODS(self):
        for method in self.SUPPORTED_HTTP_METHODS:
            allowed_method = getattr(self, method.lower(), NotImplemented)
            if allowed_method is NotImplemented:
                continue
            yield method

    status = errors.HTTP_200_OK

    headers = descriptors.Headers()

    cookies = descriptors.Cookies()

    query = descriptors.Query()

    data = descriptors.Data()

    def __init__(self, environ):
        self.environ = environ

    def __call__(self, *args, **kwargs):
        """Generates result flow."""

        callback = self.delegate()
        result, result_iterator = callback(*args, **kwargs), ()
        if not isinstance(result, basestring):
            try:
                result_iterator = iter(result)
            except TypeError:
                pass
            else:
                result = next(result_iterator)
        result = str(self.prepare_result(result) or '')
        if not result_iterator and 'Content-Length' not in self.headers:
            self.headers.set('Content-Length', len(result))
        yield result
        for chunk in result_iterator:
            yield str(self.prepare_chunk(chunk) or '')

    def delegate(self):
        """Returns callback to which request should be delegated
        (such methods as `get`, `post` and so on).

        This method is good place to implement common logic for
        all HTTP methods.
        """

        request_method = self.environ.request_method
        if request_method not in self.SUPPORTED_HTTP_METHODS:
            raise errors.HttpError(
                errors.HTTP_501_NOT_IMPLEMENTED,
                headers=(('Allow', ', '.join(self.ALLOWED_HTTP_METHODS)), )
            )
        else:
            callback = getattr(self, request_method.lower(), NotImplemented)
            if callback is NotImplemented:
                raise errors.HttpError(
                    errors.HTTP_405_METHOD_NOT_ALLOWED,
                    headers=(('Allow', ', '.join(self.ALLOWED_HTTP_METHODS)), )
                )
        return callback

    def prepare_result(self, result):
        """Prepares result before sending it to the response stream.

        If result splitted into chunks then only first chunk will be prepared
        by this method, all others will be proceeded by `prepare_chunk`.

        Unlike to `prepare_chunk` this method still allows headers modifying.
        """

        return self.prepare_chunk(result)

    def prepare_chunk(self, chunk):
        """Prepares chunk of result before sending it to the response stream.

        First chunk is prepared by `prepare_result`.

        This method doesn't allow headers modifying due to fact that they were
        already sent.
        """

        return chunk

    def options(self, *args, **kwargs):
        self.headers.set('Allow', ', '.join(self.ALLOWED_HTTP_METHODS))

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented
