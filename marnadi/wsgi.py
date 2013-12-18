import logging
import itertools

from marnadi import errors, descriptors, Route
from marnadi.descriptors.headers import Header


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
        self.routes = self.compile_routes(list(routes))

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
            headers = response_flow.headers

        start_response(status, headers)

        return response_flow  # return rest of the flow as response body

    def compile_routes(self, routes):
        for index, route in enumerate(routes):
            if not isinstance(route, Route):
                routes[index] = route = Route(*route)
            if not issubclass(route.handler, Handler):
                route.handler = self.compile_routes(list(route.handler))
        return routes

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
        for route in routes:
            if hasattr(route.path, 'match'):  # assume it's compiled regexp
                match = route.path.match(path)
                if not match:
                    continue
                match_args, match_kwargs = self.get_match_subgroups(match)
                args.extend(match_args)
                kwargs.update(match_kwargs)
                rest_path = path[match.end(0):]
            elif path.startswith(route.path):
                rest_path = path[len(route.path):]
            else:
                continue
            if isinstance(route.handler, list):
                try:
                    return self.get_handler(
                        rest_path,
                        routes=route.handler,
                        args=args,
                        kwargs=kwargs,
                    )
                except errors.HttpError:
                    pass
            if not rest_path:
                return lambda environ: route.handler.handle(
                    environ,
                    args=itertools.chain(route.args, args),
                    kwargs=dict(kwargs, **route.kwargs),
                )
        raise errors.HttpError(errors.HTTP_404_NOT_FOUND)


class HandlerProcessor(type):

    logger = logging.getLogger('marnadi')

    def __new__(mcs, name, bases, attributes):
        cls = super(HandlerProcessor, mcs).__new__(mcs, name, bases, attributes)
        for attr_name, attr_value in attributes.iteritems():
            cls.set_descriptor_name(attr_value, attr_name)
        return cls

    def __setattr__(cls, attr_name, attr_value):
        super(HandlerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_descriptor_name(attr_value, attr_name)

    def __call__(cls, *args, **kwargs):
        if cls.func is not None:
            return cls.func(*args, **kwargs)
        return super(HandlerProcessor, cls).__call__(*args, **kwargs)

    def decorator(cls, func):
        method = lambda self, *args, **kwargs: func(
            *args, **kwargs
        )
        attributes = dict(func=staticmethod(func))
        for supported_method in cls.SUPPORTED_HTTP_METHODS:
            supported_method = supported_method.lower()
            if getattr(cls, supported_method, NotImplemented) is NotImplemented:
                attributes[supported_method] = method
        return type(func.__name__, (cls, ), attributes)

    def handle(cls, environ, args=(), kwargs=None):
        try:
            handler = super(HandlerProcessor, cls).__call__(environ)
            result = handler(*args, **kwargs or {})
            chunks, first_chunk, chunked = (), '', False
            try:
                assert not isinstance(result, basestring)
                chunks = iter(result)
            except (AssertionError, TypeError):
                first_chunk = unicode(result or '').encode('utf-8')
            else:
                try:
                    first_chunk = unicode(chunks.next()).encode('utf-8')
                except StopIteration:
                    # only StopIteration exception alone should be caught
                    # at this place
                    pass
            if not handler.headers.setdefault('Content-Length'):
                try:
                    assert not (chunks and len(result) > 1)
                    handler.headers['Content-Length'] = len(first_chunk)
                except (TypeError, AssertionError):
                    handler.headers['Transfer-Encoding'] = 'chunked'
                    chunked = True
            yield handler.status
            for header, value in handler.headers.flush():
                yield header, str(value)
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
            cls.handle_exception(error)

    def handle_exception(cls, error):
        cls.logger.exception(error)
        raise errors.HttpError(info=error)

    @staticmethod
    def make_chunk(chunk, chunked=False):
        if chunked:
            return '%X\r\n%s\r\n' % (len(chunk), chunk)
        return chunk

    def __subclasscheck__(cls, subclass):
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
            raise errors.HttpError(
                errors.HTTP_501_NOT_IMPLEMENTED,
                headers=(('Allow', ', '.join(self.allowed_http_methods)), )
            )
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
            if getattr(self, method.lower(), NotImplemented) is NotImplemented:
                continue
            yield method

    def options(self, *args, **kwargs):
        self.headers['Allow'] = ', '.join(self.allowed_http_methods)

    get = NotImplemented

    head = NotImplemented

    post = NotImplemented

    put = NotImplemented

    patch = NotImplemented

    delete = NotImplemented
