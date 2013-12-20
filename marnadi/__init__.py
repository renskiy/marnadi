import collections
import importlib
import itertools

from marnadi import errors


class Lazy(object):

    __slots__ = ('_path', '_value')

    def __init__(self, path):
        if isinstance(path, basestring):
            self._value = None
            self._path = path
        else:
            self.obj = path

    def __call__(self, *args, **kwargs):
        return self.obj(*args, **kwargs)

    def __iter__(self):
        return self.obj.__iter__()

    def __str__(self):
        return str(self.obj)

    def __getitem__(self, item):
        return self.obj[item]

    def __getattr__(self, attr):
        return getattr(self.obj, attr)

    @property
    def obj(self):
        if self._value is None:
            module_name, obj_name = self._path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            self.obj = getattr(module, obj_name)
        return self._value

    @obj.setter
    def obj(self, value):
        assert value is not None, "`obj` can't be None"
        self._value = value


class Route(object):

    __slots__ = ('path', '_handler', 'args', 'kwargs')

    def __init__(self, path, handler, *args, **kwargs):
        self.path = path
        self._handler = Lazy(handler)
        self.args = args
        self.kwargs = kwargs

    @property
    def handler(self):
        return self._handler.obj

    @handler.setter
    def handler(self, value):
        self._handler.obj = value


class Header(object):

    __slots__ = ('values', 'attributes')

    def __init__(self, *values, **attributes):
        self.values = values
        self.attributes = attributes

    def __str__(self):
        return self.make_value(*self.values, **self.attributes)

    @staticmethod
    def make_value(*values, **attributes):
        return '; '.join(itertools.chain(
            values,
            (
                '%s=%s' % (attr_name, attr_value)
                for attr_name, attr_value in attributes.iteritems()
            ),
        ))


class HttpError(Exception):

    default_headers = (
        ('Content-Type', Header('text/plain', charset='utf-8')),
    )

    def __init__(self, status=errors.HTTP_500_INTERNAL_SERVER_ERROR,
                 data=None, headers=(), info=None):
        self.status = status
        self._headers = headers
        self._data = data
        self.info = info

    def __len__(self):
        return 1

    def __iter__(self):
        yield unicode(self._data or '').encode('utf-8')

    def __str__(self):
        return "%s, info: %s" % (self.status, self.info)

    @property
    def headers(self):
        headers = collections.defaultdict(list)
        default_headers = collections.defaultdict(list)
        for header, value in self._headers:
            headers[header.title()].append(value)
        for header, value in self.default_headers:
            header = header.title()
            if header not in headers:
                default_headers[header].append(value)
        return [
            (header, str(value))
            for header, values in itertools.chain(
                headers.iteritems(),
                default_headers.iteritems(),
            )
            for value in values
        ]
