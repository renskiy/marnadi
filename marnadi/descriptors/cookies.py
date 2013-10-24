import datetime
import time
import urllib

from marnadi.descriptors import Descriptor


class Cookies(Descriptor):
    """Cookies.

    Like Headers allow access to request cookies ONLY by key
    or using `get` method.
    """

    def __init__(self):
        super(Cookies, self).__init__()
        self.headers = None
        self._cookies = None

    def clone(self, handler):
        clone = super(Cookies, self).clone(handler)
        clone.headers = handler.headers
        clone._cookies = None
        return clone

    def __contains__(self, cookie):
        return cookie in self.cookies

    def __setitem__(self, *args, **kwargs):
        raise TypeError("Cookie modifying allowed only using set() method")

    def __delitem__(self, cookie):
        self.remove(cookie)

    def __getitem__(self, cookie):
        return self.cookies[cookie]

    @property
    def cookies(self):
        if self._cookies is None:
            try:
                self._cookies = dict(
                    cookie.strip().split('=', 1)
                    for cookie in self.headers['Cookie'].split(';')
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

    def get(self, cookie, default=None, decode=False):
        value = self.cookies.get(cookie, default)
        if decode:
            return self.decode(value)
        return value

    def set(self, cookie, value, expires=None, domain=None, path=None,
            secure=False, http_only=True, encode=False):
        if encode:
            value = self.encode(value)
        cookie_params = ['%s=%s' % (cookie, value)]
        if domain:
            cookie_params.append("Domain=%s" % domain)
        if path:
            cookie_params.append("Path=%s" % path)
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
        self.headers.append('Set-Cookie', '; '.join(cookie_params))

    def encode(self, value):
        return urllib.quote(value)

    def decode(self, value):
        return urllib.unquote(value)