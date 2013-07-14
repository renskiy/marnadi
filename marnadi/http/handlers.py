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

    def update_manager_name(cls, manager, name):
        if isinstance(manager, managers.Manager):
            manager.name = manager.name or name

    def __call__(cls, environ, *args, **kwargs):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            request_method = environ.request_method
            try:
                method = getattr(handler, request_method.lower())
            except AttributeError:
                # TODO should include list of allowed methods
                raise errors.HttpError(errors.HTTP_405_METHOD_NOT_ALLOWED)
            result = method(*args, **kwargs)
            result_iterator = ()
            if not isinstance(result, basestring):
                try:
                    result_iterator = iter(result)
                    result = next(result_iterator)
                except TypeError:
                    pass
            result = str(handler.transform_result(result))
            if not result_iterator:
                handler.headers.set('Content-Length', len(result))
            yield str(handler.status)
            for header, value in handler.headers:
                yield str(header), str(value)
            yield ''  # separator between headers and body
            yield result
            for chunk in result_iterator:
                yield str(handler.transform_chunk(chunk))
        except errors.HttpError:
            raise
        except:
            raise errors.HttpError


class Handler(object):
    # TODO implement way how to instantiate Handler (e.g. for testing purpose)

    __metaclass__ = HandlerProcessor

    status = errors.HTTP_200_OK

    headers = managers.Headers()

    cookies = managers.Cookies()

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
