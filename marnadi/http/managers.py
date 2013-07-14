import collections
import copy


class Manager(object):
    """Base class for all handler's managers.

    Custom managers should inherit this functionality.

    Attributes:
        name: attribute name of owner class to which this manager assigned.
        environ: Environ class object containing environment variables of
        current request.
    """

    def __init__(self, name=None):
        self.name = name
        self.environ = None

    def __get__(self, handler, handler_class):
        clone = self.clone(environ=handler.environ)
        if self.name:
            setattr(handler, self.name, clone)
        return clone

    def clone(self, **kwargs):
        clone = copy.deepcopy(self)
        clone.__dict__.update(kwargs)
        return clone


class Headers(Manager):
    """Request/response headers manager.

    Only one method `get` used to assign request headers,
    all other methods used to operate with the response headers.
    Iterating over the manager is actually iterating over the response headers.

    Attributes:
        response_headers: dict collection of response headers
    """
    # TODO implement dict-like access

    def __init__(self, response_headers=None, *args, **kwargs):
        super(Headers, self).__init__(*args, **kwargs)
        self.response_headers = collections.defaultdict(list)
        for header, value in response_headers or ():
            self.add(header, value)

    def add(self, response_header, value):
        self.response_headers[response_header].append(value)

    def get(self, request_header, default=None):
        # TODO check environ headers format
        return self.environ.get(request_header, default)

    def set(self, response_header, value):
        self.response_headers[response_header] = [value]

    def remove(self, response_header):
        del self.response_headers[response_header]

    def __iter__(self):
        # TODO disable headers modifying after calling this method
        return iter(
            (header, value)
            for header, values in self.response_headers.viewitems()
            for value in values
        )


class Cookies(Manager):
    # TODO finish implementation
    # TODO implement dict-like access

    def __init__(self, *args, **kwargs):
        super(Cookies, self).__init__(*args, **kwargs)
        self.headers = None

    def __get__(self, handler, handler_class):
        instance = super(Cookies, self).__get__(handler, handler_class)
        instance.headers = handler.headers
        return instance

    def set(self, response_cookie, value):
        # TODO add rest cookie params to argument list
        pass

    def get(self, request_cookie):
        pass

    def remove(self, response_cookie):
        pass