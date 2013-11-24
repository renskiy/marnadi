from marnadi import errors, handlers


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
                next_header = self.header(next_header)
                headers.append(next_header)
                next_header = next(response_flow)
        except errors.HttpError as response_flow:
            status = response_flow.status
            headers = map(self.header, response_flow.headers)

        start_response(status, headers)

        return response_flow  # return rest of the flow as response body

    @staticmethod
    def header(header):
        return header[0].title(), header[1]

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
        return match_args, match_kwargs

    def get_handler(self, path, routes=None, handler_args=None,
                    handler_kwargs=None):
        routes = routes or self.routes
        handler_args = handler_args or []
        handler_kwargs = handler_kwargs or {}
        for route_path, route_handler in routes:
            if hasattr(route_path, 'match'):  # assume it's compiled regexp
                match = route_path.match(path)
                if not match:
                    continue
                match_args, match_kwargs = self.get_match_subgroups(match)
                handler_args.extend(match_args)
                handler_kwargs.update(match_kwargs)
                rest_path = path[match.end(0):]
            elif path.startswith(route_path):
                rest_path = path[len(route_path):]
            else:
                continue
            if not issubclass(route_handler, handlers.Handler):
                try:
                    routes = iter(route_handler)
                    return self.get_handler(
                        rest_path,
                        routes=routes,
                        handler_args=handler_args,
                        handler_kwargs=handler_kwargs,
                    )
                except (AttributeError, TypeError):
                    pass
            if not rest_path:
                return lambda environ: route_handler(
                    environ,
                    handler_args=handler_args,
                    handler_kwargs=handler_kwargs,
                )
        raise errors.HttpError(errors.HTTP_404_NOT_FOUND)
