from marnadi import errors


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

    def __init__(self, routes=None):
        self.routes = routes or ()

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
                next_header = (
                    next_header[0].title(),
                    next_header[1],
                )
                headers.append(next_header)
                next_header = next(response_flow)
        except errors.HttpError as response_flow:
            status, headers = response_flow.status, list(response_flow.headers)

        start_response(status, headers)

        return response_flow  # return rest of the flow as response body

    @staticmethod
    def get_path(environ):
        return environ.path_info

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

    def get_handler(self, path, routes=None, *args, **kwargs):
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
                routes = iter(handler)
                return self.get_handler(
                    rest_path,
                    routes=routes,
                    *args, **kwargs
                )
            if not rest_path:
                return lambda environ: handler(environ, *args, **kwargs)
        raise errors.HttpError(errors.HTTP_404_NOT_FOUND)
