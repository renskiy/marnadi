import collections
import copy
import datetime
import time
import weakref

from marnadi.utils import cached_property, CachedDescriptor


class CookieJar(collections.MutableMapping):
    """Cookies - dict-like object allowing to get/set HTTP cookies"""

    if hasattr(collections.MutableMapping, '__slots__'):
        __slots__ = ('_response', 'domain', 'path', 'expires', 'secure',
                     'http_only', '__weakref__')

    def __init__(self, response, domain=None, path=None, expires=None,
                 secure=False, http_only=True, ):
        self._response = weakref.ref(response)
        self.domain = domain
        self.path = path
        self.expires = expires
        self.secure = secure
        self.http_only = http_only

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    __ne__ = object.__ne__

    def __setitem__(self, cookie, value):
        self.set(cookie, value)
        if value is None:
            self.request_cookies.pop(cookie, None)
        else:
            self.request_cookies[cookie] = value

    def __delitem__(self, cookie):
        self.remove(cookie)
        del self.request_cookies[cookie]

    def __getitem__(self, cookie):
        return self.request_cookies[cookie]

    def __iter__(self):
        return iter(self.request_cookies)

    def __len__(self):
        return len(self.request_cookies)

    @property
    def response(self):
        response = self._response()
        if response is not None:
            return response
        raise ValueError("CookieJar used outside of response scope")

    @cached_property
    def request_cookies(self):
        try:
            return dict(
                cookie.strip().split('=', 1)
                for cookie in self.response.request.headers['Cookie'].split(';')
            )
        except (KeyError, ValueError):
            return {}

    def clear(self, *cookies):
        if cookies:
            for cookie in cookies:
                self.pop(cookie, None)
        else:
            super(CookieJar, self).clear()

    def remove(self, cookie, domain=None, path=None, secure=None,
               http_only=None):
        self.set(cookie, '', expires=datetime.datetime(1980, 1, 1),
                 domain=domain, path=path, secure=secure, http_only=http_only)

    def set(self, cookie, value, expires=None, domain=None, path=None,
            secure=None, http_only=None):
        if value is None:
            return self.remove(cookie, domain=domain, path=path,
                               secure=secure, http_only=http_only)
        domain = self.domain if domain is None else domain
        path = self.path if path is None else path
        expires = self.expires if expires is None else expires
        secure = self.secure if secure is None else secure
        http_only = self.http_only if http_only is None else http_only

        cookie_params = ['%s=%s' % (cookie, value)]
        domain is not None and cookie_params.append("Domain=%s" % domain)
        path is not None and cookie_params.append("Path=%s" % path)
        if expires is not None:
            try:
                # try to use `expires` as timedelta
                expires += datetime.datetime.now()
            except TypeError:
                pass
            if isinstance(expires, datetime.datetime):
                struct_time = (
                    time.gmtime(time.mktime(expires.timetuple()))
                    if expires.tzinfo is None else
                    time.localtime(time.mktime(expires.utctimetuple()))
                )
                expires = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                        struct_time)
            cookie_params.append("Expires=%s" % expires)
        secure and cookie_params.append("Secure")
        http_only and cookie_params.append("HttpOnly")
        self.response.headers.append('Set-Cookie', '; '.join(cookie_params))


class Cookies(CachedDescriptor):

    __slots__ = 'domain', 'path', 'expires', 'secure', 'http_only'

    def __init__(self, domain=None, path=None, expires=None, secure=False,
                 http_only=True):
        super(Cookies, self).__init__()
        self.domain = domain
        self.path = path
        self.expires = expires
        self.secure = secure
        self.http_only = http_only

    def get_value(self, response):
        return CookieJar(
            response=response,
            domain=self.domain,
            path=self.path,
            expires=copy.copy(self.expires),
            secure=self.secure,
            http_only=self.http_only,
        )
