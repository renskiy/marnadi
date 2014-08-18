import collections
import functools
import itertools
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from marnadi import Route, descriptors, Header
from marnadi.errors import HttpError
from marnadi.handlers import Handler
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
    def content_type(self):
        try:
            parts = iter(self['CONTENT_TYPE'].split(';'))
            return Header(next(parts).strip(), **dict(
                map(str.strip, option.split('='))
                for option in parts
            ))
        except KeyError:
            raise AttributeError("content_type is not provided")

    @property
    def content_length(self):
        try:
            return int(self['CONTENT_LENGTH'])
        except KeyError:
            raise AttributeError("content_length is not provided")

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

    @cached_property
    def query(self):
        try:
            return dict(parse.parse_qsl(
                self['QUERY_STRING'],
                keep_blank_values=True,
            ))
        except KeyError:
            return {}

    data = descriptors.Data(
        (
            'application/json',
            'marnadi.descriptors.data.decoders.application.json.Decoder',
        ),
        (
            'application/x-www-form-urlencoded',
            'marnadi.descriptors.data.decoders' +
            '.application.x_www_form_urlencoded.decoder',
        ),
    )


class App(object):
    """WSGI application class.

    Instance of this class used as entry point for WSGI requests. Using
    provided routes list it can determine which handler should be called.

    Args:
        routes (iterable): list of :class:`Route`.
    """

    __slots__ = 'routes', 'routes_map'

    def __init__(self, routes=()):
        self.routes_map = {}
        self.routes = self.compile_routes(routes)

    def __call__(self, environ, start_response):
        try:
            request = self.make_request_object(environ)
            handler = self.get_handler(request.path)
            handler.send(None)  # start coroutine
            return handler.send((request, start_response))
        except HttpError as error:
            start_response(
                error.status,
                list(error.headers.items(stringify=True))
            )
            return error

    @staticmethod
    def make_request_object(environ):
        return Request(environ)

    def compile_routes(self, routes, parents=()):
        callback = functools.partial(self.compile_route, parents=parents)
        return list(map(callback, routes))

    def compile_route(self, route, parents=()):
        assert isinstance(route, Route)
        parents = parents + (route, )
        if route.name:
            self.routes_map[route.name] = parents
        if isinstance(route.handler, Handler):
            return route
        try:
            route.handler = self.compile_routes(route.handler, parents=parents)
        except TypeError:
            raise TypeError(
                "Route's handler must be either subclass of Handler " +
                "or sequence of nested subroutes")
        return route

    def route(self, path, name=None, params=None, patterns=None):
        def _decorator(handler):
            route = Route(
                path, handler, name=name, params=params, patterns=patterns)
            self.routes.append(self.compile_route(route))
            return handler
        return _decorator

    def make_path(self, *route_name, **params):
        if len(route_name) != 1:
            raise TypeError(
                "either route_name isn't provided or it isn't a single value")
        return ''.join(
            route.restore_path(**params)
            for route in self.routes_map[route_name[0]]
        )

    def get_handler(self, path, routes=None, params=None):
        """Return handler according to the given path.

        Note:
            If you wish for example automatically redirect all requests
            without trailing slash in URL to URL with persisting one you may
            override this method by raising `HttpError` with 301 status and
            necessary 'Location' header when needed.
        """
        routes = routes or self.routes
        params = params or {}
        for route in routes:
            match = route.match(path)
            if not match:
                continue
            rest_path, url_params = match
            if isinstance(route.handler, list):
                try:
                    return self.get_handler(
                        rest_path,
                        routes=route.handler,
                        params=self._merge_dicts(
                            params.copy(), route.params, url_params),
                    )
                except HttpError:
                    continue
            if not rest_path:
                return route.handler.start(**self._merge_dicts(
                    params, route.params, url_params))
        raise HttpError('404 Not Found')  # matching route not found

    @staticmethod
    def _merge_dicts(target, *sources):
        for source in sources:
            target.update(source)
        return target
