import collections
import functools
import itertools
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from marnadi import http
from marnadi.route import Routes
from marnadi.utils import cached_property


class Request(collections.Mapping):
    """WSGI request.

    Args:
        environ (dict): PEP-3333 WSGI environ dict.
    """

    if hasattr(collections.Mapping, '__slots__'):
        __slots__ = 'environ', '__weakref__'

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    __ne__ = object.__ne__

    def __init__(self, environ):
        self.environ = environ

    def __getitem__(self, key):
        return self.environ[key]

    def __iter__(self):
        return iter(self.environ)

    def __len__(self):
        return len(self.environ)

    @property
    def input(self):
        return self['wsgi.input']

    @property
    def method(self):
        return self['REQUEST_METHOD']

    @property
    def path(self):
        return self['PATH_INFO']

    @property
    def query_string(self):
        return self.get('QUERY_STRING')

    @property
    def remote_addr(self):
        return self.get('REMOTE_ADDR')

    @property
    def remote_host(self):
        return self.get('REMOTE_HOST')

    @property
    def content_length(self):
        return int(self.get('CONTENT_LENGTH', 0))

    @cached_property
    def content_type(self):
        try:
            parts = iter(self['CONTENT_TYPE'].split(';'))
            return http.Header(next(parts).strip(), **dict(
                map(str.strip, part.split('=', 1))
                for part in parts
            ))
        except KeyError:
            pass

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
                self.query_string,
                keep_blank_values=True,
            ))
        except KeyError:
            return {}

    data = http.Data(
        (
            'application/json',
            'marnadi.http.data.decoders.application.json.Decoder',
        ),
        (
            'application/x-www-form-urlencoded',
            'marnadi.http.data.decoders' +
            '.application.x_www_form_urlencoded.Decoder',
        ),
    )


class App(object):
    """WSGI application class.

    Instance of this class used as entry point for WSGI requests. Using
    provided routes list it can determine which handler should be called.

    Args:
        routes (iterable): list of :class:`Route`.
    """

    __slots__ = 'routes', 'route_map'

    def __init__(self, routes=()):
        self.route_map = {}
        self.routes = Routes(routes)
        self.build_route_map()

    def __call__(self, environ, start_response):
        try:
            request = self.make_request_object(environ)
            handler = self.get_handler(request.path)
            response = handler(self, request)
        except http.Error as error:
            response = error
        start_response(
            response.status,
            list(response.headers.items(stringify=True))
        )
        return response

    @staticmethod
    def make_request_object(environ):
        return Request(environ)  # TODO make request_type as instance attribute

    def build_route_map(self, routes=None, parents=()):
        routes = self.routes if routes is None else routes
        for route in routes:
            self.register_route(route, parents=parents)

    def register_route(self, route, parents=()):
        parents = parents + (route, )
        if route.name:
            self.route_map[route.name] = parents
        self.build_route_map(route.routes, parents=parents)

    def route(self, path, **route_params):
        return self.routes.route(path, **route_params)

    def make_path(self, *route_name, **params):
        assert len(route_name) == 1
        return ''.join(
            route.restore_path(**params)
            for route in self.route_map[route_name[0]]
        )

    def get_handler(self, path, routes=None, params=None):
        """Return handler according to the given path.

        Note:
            If you wish for example automatically redirect all requests
            without trailing slash in URL to URL with persisting one you may
            override this method by raising `http.Error` with 301 status and
            necessary 'Location' header when needed.
        """
        routes = routes or self.routes
        params = params or {}
        for route in routes:
            match = route.match(path)
            if not match:
                continue
            rest_path, route_params = match
            if not rest_path:
                if route.handler:
                    params.update(route_params)
                    return functools.partial(route.handler.start, **params)
            else:
                try:
                    return self.get_handler(
                        rest_path,
                        routes=route.routes,
                        params=dict(params, **route_params),
                    )
                except http.Error:
                    pass  # wrong way raises "404 Not Found" at the end
        raise http.Error('404 Not Found')  # matching route not found
