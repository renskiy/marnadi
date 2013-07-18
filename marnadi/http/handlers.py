from marnadi.http import errors, managers


class HandlerProcessor(managers.ManagerProcessor):

    def __call__(cls, environ, *args, **kwargs):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            request_method = environ.request_method
            if request_method not in handler.SUPPORTED_HTTP_METHODS:
                handler.status = errors.HTTP_501_NOT_IMPLEMENTED
                callback = handler.options
            else:
                callback = getattr(
                    handler,
                    request_method.lower(),
                    NotImplemented
                )
                if callback is NotImplemented:
                    handler.status = errors.HTTP_405_METHOD_NOT_ALLOWED
                    callback = handler.options
            result = callback(*args, **kwargs)
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

    request = managers.Request()

    def __init__(self, environ):
        self.environ = environ

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

    def options(self, *args, **kwargs):
        self.headers.set('Allow', ', '.join(self.ALLOWED_HTTP_METHODS))

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented
