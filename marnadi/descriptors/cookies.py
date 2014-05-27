import collections
import copy
import datetime
import time

from marnadi.descriptors import Descriptor


class Cookies(collections.MutableMapping, Descriptor):
    """Cookies - dict-like object allowing to get/set HTTP cookies"""

    def __init__(self, domain=None, path=None, expires=None,
                 secure=False, http_only=True):
        super(Cookies, self).__init__()
        self._headers = None
        self._cookies = None
        self.domain = domain
        self.path = path
        self.expires = expires
        self.secure = secure
        self.http_only = http_only

    def get_value(self, handler):
        value = super(Cookies, self).get_value(handler)
        value._headers = handler.headers
        return value

    def __copy__(self):
        return self.__class__(
            domain=self.domain,
            path=self.path,
            expires=copy.copy(self.expires),
            secure=self.secure,
            http_only=self.http_only,
        )

    def __setitem__(self, cookie, value):
        self.set(cookie, value)
        if value is None:
            self.cookies.pop(cookie, None)
        else:
            self.cookies[cookie] = value

    def __delitem__(self, cookie):
        self.remove(cookie)
        del self.cookies[cookie]

    def __getitem__(self, cookie):
        return self.cookies[cookie]

    def __iter__(self):
        return iter(self.cookies)

    def __len__(self):
        return len(self.cookies)

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

    def clear(self, *cookies):
        if cookies:
            for cookie in cookies:
                self.pop(cookie, None)
        else:
            super(Cookies, self).clear()

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
        self._headers.append('Set-Cookie', '; '.join(cookie_params))
