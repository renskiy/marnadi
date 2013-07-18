import collections
import copy


class ManagerProcessor(type):

    def __setattr__(cls, attr_name, attr_value):
        super(ManagerProcessor, cls).__setattr__(attr_name, attr_value)
        cls.set_manager_name(attr_value, attr_name)

    def set_manager_name(cls, manager, name):
        if isinstance(manager, Manager):
            manager.name = manager.name or name
            for attr_name, attr_value \
                    in manager.__class__.__dict__.itervalues():
                cls.set_manager_name(attr_value, attr_name)


class Manager(object):
    """Base class for all handler's managers.

    Custom managers should inherit this functionality.

    Attributes:
        name: attribute name of owner class to which this manager assigned.
        environ: Environ class object containing environment variables of
        current request.
    """

    __metaclass__ = ManagerProcessor

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.environ = None

    def __get__(self, owner, owner_class):
        clone = self.clone(environ=owner.environ)
        if self.name:
            setattr(owner, self.name, clone)
        return clone

    def clone(self, **kwargs):
        clone = copy.deepcopy(self)
        clone.__dict__.update(kwargs)
        return clone


class Headers(Manager):
    """Request/response headers manager.

    All read-access methods (except of `__iter__`) are used to access request
    headers, all other methods are used to modify the response headers.

    Once iteration over itself has started there is no more opportunity
    to modify list of response headers, so DO NOT iterate it until you set all
    necessary headers.
    """

    def __init__(self, *response_headers, **kwargs):
        super(Headers, self).__init__(**kwargs)
        self._headers_sent = False
        self._response_headers = collections.defaultdict(list)
        for header, value in response_headers or ():
            self.add(header, value)

    def __getitem__(self, request_header):
        result = self.get(request_header)
        if result is None:
            raise KeyError
        return result

    def __iter__(self):
        self._next = (
            (header, value)
            for header, values in self._response_headers.viewitems()
            for value in values
        ).next
        return self

    def next(self):
        self._headers_sent = True
        return self._next()

    @property
    def response_headers(self):
        assert not self._headers_sent, "headers been already sent"
        return self._response_headers

    def add(self, response_header, value):
        self.response_headers[response_header].append(value)

    def extend(self, response_headers, replace=False):
        replaced_headers = []
        for response_header, value in response_headers:
            if replace and response_header not in replaced_headers:
                replaced_headers.append(response_header)
                self.remove(response_header)
            self.add(response_header, value)

    def get(self, request_header, default=None):
        getattr(self.environ, 'http_%s' % request_header.lower(), default)

    def set(self, response_header, value):
        self.response_headers[response_header] = [value]

    def remove(self, response_header):
        del self.response_headers[response_header]


class Query(Manager):
    # TODO finish implementation

    pass


class Body(Manager):
    # TODO finish implementation

    pass


class Request(Manager):

    query = Query()

    body = Body()


class Cookies(Manager):
    # TODO finish implementation
    # TODO implement dict-like access

    def __init__(self, **kwargs):
        super(Cookies, self).__init__(**kwargs)
        self.headers = None

    def __get__(self, handler, handler_class):
        instance = super(Cookies, self).__get__(handler, handler_class)
        instance.headers = handler.headers
        return instance

    def set(
        self,
        response_cookie,
        value,
        expires=None,
        domain=None,
        path=None,
        secure=False,
        http_only=True,
    ):
        pass

    def get(self, request_cookie):
        pass

    def remove(self, response_cookie):
        pass