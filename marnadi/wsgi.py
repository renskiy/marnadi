import functools
import itertools
import UserDict

from marnadi import Route, Handler
from marnadi.errors import HttpError


class Environ(UserDict.DictMixin, object):
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
            handler.send(None)  # start coroutine
            return handler.send((environ, start_response))
        except HttpError as error:
            start_response(error.status, error.headers)
            return error

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

    def _route(self, *args, **kwargs):
        def _decorator(handler):
            route = Route(path, handler, *args, **kwargs)
            compiled_route = self.compile_route(route)
            self.routes.append(compiled_route)
            return handler
        try:
            path, args = args[0], args[1:]
        except IndexError:
            raise ValueError(
                "Requires path as first argument "
                "(it must be an arg, not kwarg)"
            )
        return _decorator

    @functools.partial(lambda real, dummy: functools.wraps(dummy)(real), _route)
    def route(self, path, *args, **kwargs):
        pass  # this method is dummy, the real one is `_route`

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
                # (see tests.test_wsgi.test_get_handler__non_trivial_situation)
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
                except HttpError:
                    pass
            if not rest_path:
                args = itertools.chain(route.args, args)
                kwargs = dict(kwargs, **route.kwargs)
                return route.handler.handle(*args, **kwargs)
        raise HttpError('404 Not Found')
