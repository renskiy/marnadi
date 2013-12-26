import itertools
import UserDict

from marnadi import errors, Route
from marnadi.handlers import Handler


class Environ(object, UserDict.DictMixin):
    """WSGI environ object class.

    Standard WSGI environ dict wrapped by class additionally allowing
    access to dict values using instance attributes.

    Args:
        environ (dict): original WSGI dict.
    """

    def __init__(self, environ):
        self._environ = environ

    def __getattr__(self, attr_name):
        try:
            attr_value = self._environ.get(attr_name)
            if attr_value is None:
                return self._environ[attr_name.upper()]
            return attr_value
        except KeyError:
            raise AttributeError

    def __getitem__(self, key):
        return self._environ[key]

    def __iter__(self):  # native implementation is better
        return self._environ.__iter__()

    def keys(self):
        return self._environ.keys()

    @property
    def http_content_type(self):
        return self.content_type

    @property
    def http_content_length(self):
        return self.content_length


class App(object):
    """WSGI application class.

    Instance of this class used as entry point for WSGI requests. Using
    provided routes list it can determine which handler should be called.

    Args:
        routes (iterable): routes list each element of which can be either
            instance of :class:`Route` or sequence of one's arguments.
    """

    def __init__(self, routes=()):
        self.routes = self.compile_routes(routes)

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
        return map(self.compile_route, routes)

    def compile_route(self, route):
        if not isinstance(route, Route):
            route = Route(*route)
        try:
            if issubclass(route.handler, Handler):
                return route
        except TypeError:
            pass
        try:
            route.handler = self.compile_routes(route.handler)
        except TypeError:
            raise TypeError(
                "Route's handler must be either subclass of Handler "
                "or sequence of nested subroutes"
            )
        return route

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
        raise errors.HttpError('404 Not Found')
