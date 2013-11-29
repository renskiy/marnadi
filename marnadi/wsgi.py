import functools
import logging

from marnadi import errors, descriptors, Lazy

logger = logging.getLogger('marnadi')


class Environ(dict):

    def __getattr__(self, name):
        try:
            attr = self.get(name)
            return attr is None and self[name.upper()] or attr
        except KeyError:
            raise AttributeError

    @property
    def http_content_type(self):
        return self.content_type

    @property
    def http_content_length(self):
        return self.content_length


class App(object):

    def __init__(self, routes=()):
        self.routes = routes

    def __call__(self, environ, start_response):
        try:
            environ = Environ(environ)
            path = self.get_path(environ)
            handler = self.get_handler(path)
            response = handler(environ)
            response_flow = iter(response)
            headers = []
            status = next(response_flow)
            next_header = next(response_flow)
            while next_header:
                headers.append(next_header)
                next_header = next(response_flow)
        except errors.HttpError as response_flow:
            status = response_flow.status
            headers = list(response_flow.headers)

        start_response(status, headers)

        return response_flow  # return rest of the flow as response body

    @staticmethod
    def get_path(environ):
        return environ.path_info

    @staticmethod
    def get_match_subgroups(match_object):
        args = match_object.groups()
        kwargs = match_object.groupdict()
        if kwargs:
            if len(args) == len(kwargs):
                args = ()
            else:
                # mixing simple and named subgroups is bad idea
                # because of non-trivial logic of distinguishing them,
                # use it only if you're sure
                args = list(args)
                for kwarg in kwargs.itervalues():
                    args.remove(kwarg)
        return args, kwargs

    def get_handler(self, path, routes=None, args=None, kwargs=None):
        routes = routes or self.routes
        args = args or []
        kwargs = kwargs or {}
        for route_path, route_handler in routes:
            if hasattr(route_path, 'match'):  # assume it's compiled regexp
                match = route_path.match(path)
                if not match:
                    continue
                match_args, match_kwargs = self.get_match_subgroups(match)
                args.extend(match_args)
                kwargs.update(match_kwargs)
                rest_path = path[match.end(0):]
            elif path.startswith(route_path):
                rest_path = path[len(route_path):]
            else:
                continue
            if not issubclass(route_handler, Handler):
                try:
                    routes = iter(route_handler)
                    return self.get_handler(
                        rest_path,
                        routes=routes,
                        args=args,
                        kwargs=kwargs,
                    )
                except (AttributeError, TypeError):
                    pass
            if not rest_path:
                return lambda environ: route_handler(
                    environ,
                    args=args,
                    kwargs=kwargs,
                )
        raise errors.HttpError(errors.HTTP_404_NOT_FOUND)


class HandlerProcessor(type):

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_descriptor_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_descriptor_name(attr_value, attr_name)

    def __call__(cls, environ, **kwargs):
        if isinstance(environ, Environ):
            return cls.as_class(environ, **kwargs)
        assert len(kwargs) == 0, "invalid usage"
        return cls.as_decorator(func=environ)

    def as_decorator(cls, func):
        return functools.wraps(func)(lambda environ, args=(), kwargs=None: cls(
            environ,
            args=args,
            kwargs=kwargs,
            callback=func,
        ))

    def as_class(cls, environ, args=(), kwargs=None, callback=None):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ, callback)
            result = handler(*args, **kwargs or {})
            chunks, first_chunk, chunked = (), '', False
            try:
                assert not isinstance(result, basestring)
                chunks = iter(result)
            except (AssertionError, TypeError):
                first_chunk = result = unicode(result or '').encode('utf-8')
            else:
                try:
                    first_chunk = unicode(chunks.next()).encode('utf-8')
                except StopIteration:
                    # only StopIteration exceptions should be caught
                    # at this place
                    pass
            try:
                handler.headers.set('Content-Length', len(result))
            except TypeError:
                handler.headers.set('Transfer-Encoding', 'chunked')
                chunked = True
            yield str(handler.status)
            for header in handler.headers:
                yield tuple(map(str, header))
            yield  # separator between headers and body
            if first_chunk:
                yield cls.make_chunk(first_chunk, chunked)
            for next_chunk in chunks:
                next_chunk = unicode(next_chunk).encode('utf-8')
                if next_chunk:
                    yield cls.make_chunk(next_chunk, chunked)
            yield cls.make_chunk('', chunked)  # end of stream
        except errors.HttpError:
            raise
        except Exception as error:
            logger.exception(error)
            raise errors.HttpError

    @staticmethod
    def make_chunk(chunk, chunked=False):
        if chunked:
            return hex(len(chunk))[2:].upper() + '\r\n' + chunk + '\r\n'
        return chunk

    def __subclasscheck__(cls, subclass):
        if isinstance(subclass, Lazy):
            subclass = subclass.obj
        try:
            return super(HandlerProcessor, cls).__subclasscheck__(subclass)
        except TypeError:
            return False

    @staticmethod
    def set_descriptor_name(descriptor, attr_name):
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
        ('application/json', 'marnadi.mime.application.json.Decoder'),
        ('application/x-www-form-urlencoded',
            'marnadi.mime.application.x_www_form_urlencoded.Decoder'),
    )

    def __init__(self, environ, callback=None):
        self.environ = environ
        self.callback = callback

    def __call__(self, *args, **kwargs):
        request_method = self.environ.request_method
        if request_method not in self.SUPPORTED_HTTP_METHODS:
            raise errors.HttpError(
                errors.HTTP_501_NOT_IMPLEMENTED,
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        callback = getattr(self, request_method.lower(), None) or self.callback
        if callback is None:
            raise errors.HttpError(
                errors.HTTP_405_METHOD_NOT_ALLOWED,
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
        return callback(*args, **kwargs)

    @property
    def allowed_http_methods(self):
        for method in self.SUPPORTED_HTTP_METHODS:
            allowed = self.callback or getattr(self, method.lower(), None)
            if allowed:
                yield method

    def options(self, *args, **kwargs):
        self.headers.set('Allow', ', '.join(self.allowed_http_methods))

    get = None

    head = None

    post = None

    put = None

    patch = None

    delete = None
