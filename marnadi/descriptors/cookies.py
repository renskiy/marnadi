import copy
import datetime
import time
import UserDict

from marnadi.descriptors import Descriptor


class Cookies(Descriptor, UserDict.DictMixin):
    """Cookies.

    Like Headers allow access to request cookies ONLY by key
    or using `get` method.
    """

    def __init__(self, domain=None, path=None, expires=None):
        super(Cookies, self).__init__()
        self._headers = None
        self._cookies = None
        self.domain = domain
        self.path = path
        self.expires = expires

    def get_value(self, handler):
        value = super(Cookies, self).get_value(handler)
        value._headers = handler.headers
        return value

    def __copy__(self):
        return self.__class__(
            domain=self.domain,
            path=self.path,
            expires=copy.copy(self.expires),
        )

    def __setitem__(self, cookie, value):
        self.set(cookie, value)

    def __delitem__(self, cookie):
        self.remove(cookie)

    def __getitem__(self, cookie):
        return self.cookies[cookie]

    def keys(self):
        return self.cookies.keys()

    @property
    def cookies(self):
        if self._cookies is None:
            try:
                self._cookies = dict(
                    cookie.strip().split('=', 1)
                    for cookie in self._headers['Cookie'].split(';')
                )
            except KeyError:
                self._cookies = {}
        return self._cookies

    def remove(self, cookie, domain=None, path=None):
        self.set(
            cookie,
            '',
            expires=datetime.datetime(1980, 1, 1),
            domain=domain,
            path=path
        )

    def set(self, cookie, value, expires=None, domain=None, path=None,
            secure=False, http_only=True):
        domain = domain or self.domain
        path = path or self.path
        expires = expires or self.expires
        cookie_params = ['%s=%s' % (cookie, value)]
        if domain:
            cookie_params.append("Domain=%s" % domain)
        if path:
            cookie_params.append("Path=%s" % path)
        try:
            expires = datetime.datetime.now() + expires
        except TypeError:
            pass
        if isinstance(expires, datetime.datetime):
            struct_time = (
                time.gmtime(time.mktime(expires.timetuple()))
                if expires.tzinfo is None else
                time.localtime(time.mktime(expires.utctimetuple()))
            )
            cookie_params.append(
                "Expires=%s" %
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", struct_time)
            )
        if secure:
            cookie_params.append("Secure")
        if http_only:
            cookie_params.append("HttpOnly")
        self._headers.append('Set-Cookie', '; '.join(cookie_params))
