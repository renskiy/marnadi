import collections
import copy
import functools
import itertools
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from marnadi import Route, Handler, descriptors
from marnadi.errors import HttpError
from marnadi.utils import cached_property


class Request(collections.Mapping):
    """WSGI request.

    Args:
        environ (dict): PEP-3333 WSGI environ dict.
    """

    if hasattr(collections.Mapping, '__slots__'):
        __slots__ = '_environ', '__weakref__'

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    __ne__ = object.__ne__

    def __init__(self, environ):
        self._environ = environ

    def __getitem__(self, key):
        return self._environ[key]

    def __iter__(self):
        return iter(self._environ)

    def __len__(self):
        return len(self._environ)

    @property
    def input(self):
        return self['wsgi.input']

    @property
    def method(self):
        return self['REQUEST_METHOD']

    @property
    def path(self):
        return self['PATH_INFO']

    @cached_property
    def headers(self):
        return {
            name.title().replace('_', '-'): value
            for name, value in
            itertools.chain(
                (
                    (env_key, self[env_key])
                    for env_key in ('CONTENT_TYPE', 'CONTENT_LENGTH')
                    if env_key in self
                ),
                (
                    (env_key[5:], env_value)
                    for env_key, env_value in self.items()
                    if env_key.startswith('HTTP_')
                ),
            )
        }

    def split_header(self, header):
        """Splits header into value and options."""
        try:
            full_value = self.headers[header]
            parts = iter(full_value.split(';'))
            value = next(parts)
            return value, dict(
                (lambda p, v='': (p.strip(), v.strip('"')))(
                    *param.split('=', 1)
                )
                for param in parts
            )
        except KeyError:
            return None, {}

    @cached_property
    def query(self):
        try:
            return parse.parse_qsl(
                self['QUERY_STRING'],
                keep_blank_values=True,
            )
        except KeyError:
            return ()

    data = descriptors.Data(
        (
            'application/json',
            'marnadi.descriptors.data.decoders.application.json.Decoder',
        ),
        (
            'application/x-www-form-urlencoded',
            'marnadi.descriptors.data.decoders' +
            '.application.x_www_form_urlencoded.Decoder',
        ),
    )


class App(object):
    """WSGI application class.

    Instance of this class used as entry point for WSGI requests. Using
    provided routes list it can determine which handler should be called.

    Args:
        routes (iterable): routes list each element of which can be either
            instance of :class:`Route` or sequence of one's arguments.
    """

    __slots__ = 'routes',

    def __init__(self, routes=()):
        self.routes = self.compile_routes(routes)

    def __call__(self, environ, start_response):
        try:
            request = Request(environ)
            handler = self.get_handler(request.path)
            handler.send(None)  # start coroutine
            return handler.send((request, start_response))
        except HttpError as error:
            start_response(error.status, error.headers)
            return error

    def compile_routes(self, routes):
        return list(map(self.compile_route, routes))

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
                "or sequence of nested subroutes")
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
                "(it must be an arg, not kwarg)")
        return _decorator

    @functools.partial(lambda real, dummy: functools.wraps(dummy)(real), _route)
    def route(self, path, *args, **kwargs):
        pass  # this method is dummy, the real one is `_route`

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
        args, kwargs = args or [], kwargs or {}
        for route in routes:
            if hasattr(route.path, 'match'):  # assume it's compiled regexp
                match = route.path.match(path)
                if not match:
                    continue
                match_args, match_kwargs = self.get_match_subgroups(match)
                rest_path = path[match.end(0):]
            elif path.startswith(route.path):
                rest_path = path[len(route.path):]
                match_args = match_kwargs = ()
            else:
                continue
            _args, _kwargs = copy.copy(args), copy.copy(kwargs)
            _args.extend(route.args)
            _args.extend(match_args)
            _kwargs.update(route.kwargs)
            _kwargs.update(match_kwargs)
            if isinstance(route.handler, list):
                try:
                    return self.get_handler(
                        rest_path,
                        routes=route.handler,
                        args=_args,
                        kwargs=_kwargs,
                    )
                except HttpError:
                    continue
            if not rest_path:
                return route.handler.handle(*_args, **_kwargs)
        raise HttpError('404 Not Found')
