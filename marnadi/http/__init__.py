import functools

from marnadi.http import errors


class Status:
    # TODO finish implementation

    HTTP_200_OK = '200 OK'

    HTTP_405_METHOD_NOT_ALLOWED = '405 Method Not Allowed'


class Environ(object):
    # TODO finish implementation

    def __init__(self, environ):
        self.environ = environ


class App(object):

    def __init__(self, routes):
        self.routes = routes

    @staticmethod
    def get_path(environ):
        # TODO finish implementation
        return '/'

    @staticmethod
    def get_match_subgroups(match_object):
        match_args = match_object.groups()
        match_kwargs = match_object.groupdict()
        if match_kwargs:
            if len(match_args) == len(match_kwargs):
                match_args = ()
            else:
                # mixing simple and named subgroups is bad idea
                # because of non-trivial logic of distinguishing them,
                # use it only if you're sure
                match_args = list(match_args)
                for kwarg in match_kwargs.itervalues():
                    match_args.remove(kwarg)
                match_args = tuple(match_args)
        return match_args, match_kwargs

    def get_handler(self, path=None, routes=None, *args, **kwargs):
        if routes is None:
            routes = self.routes
        for route_path, handler in routes:
            if hasattr(route_path, 'match'):  # assume it's compiled regexp
                match = route_path.match(path)
                if not match:
                    continue
                match_args, match_kwargs = self.get_match_subgroups(match)
                args += match_args
                kwargs.update(match_kwargs)
                rest_path = path[match.end(0):]
            elif path.startswith(route_path):
                rest_path = path[len(route_path):]
            else:
                continue
            if not callable(handler):
                return self.get_handler(
                    path=rest_path,
                    routes=handler,
                    *args, **kwargs
                )
            if not path:
                return functools.partial(handler, *args, **kwargs)
        # TODO raise HTTP 404 error

    def __call__(self, environ, start_response):
        try:
            path = self.get_path(environ)
            handler = self.get_handler(path)
            response = handler.func(
                environ,
                *handler.args,
                **handler.keywords or {}
            )
            response_flow = iter(response)
            headers = []
            status = next(response_flow)
            header = next(response_flow)
            while header:
                headers.append(header)
                header = next(response_flow)
        except errors.HttpError as http_error:
            status, headers = http_error.status, http_error.headers
            response_flow = http_error

        start_response(status, headers)

        # return rest flow as response body
        return response_flow