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

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
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

    Only `get` method alone used to access request headers,
    all other methods used to operate with the response headers.

    Once iteration over itself has been completed there is no more opportunity
    to modify list of response headers, so DO NOT iterate it until you set all
    necessary headers.
    """
    # TODO implement dict-like access

    def __init__(self, *response_headers, **kwargs):
        super(Headers, self).__init__(**kwargs)
        self._headers_sent = False
        self._response_headers = collections.defaultdict(list)
        for header, value in response_headers or ():
            self.add(header, value)

    @property
    def response_headers(self):
        assert not self._headers_sent, "headers been already sent"
        return self._response_headers

    def add(self, response_header, value):
        self.response_headers[response_header].append(value)

    def get(self, request_header, default=None):
        getattr(self.environ, 'http_%s' % request_header.lower(), default)

    def set(self, response_header, value):
        self.response_headers[response_header] = [value]

    def remove(self, response_header):
        del self.response_headers[response_header]

    def __iter__(self):
        self._next = (
            (header, value)
            for header, values in self._response_headers.viewitems()
            for value in values
        ).next
        return self

    def next(self):
        try:
            return self._next()
        except StopIteration:
            self._headers_sent = True
            raise


class Cookies(Manager):
    # TODO finish implementation
    # TODO implement dict-like access

    def __init__(self, name=None):
        super(Cookies, self).__init__(name=name)
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