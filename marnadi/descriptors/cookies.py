import datetime
import urllib
import pytz

from marnadi.descriptors import Descriptor


class Cookies(Descriptor):
    """Cookies.

    Like Headers allow access to request cookies ONLY by key
    or using `get` method.
    """

    def __init__(self, **kwargs):
        super(Cookies, self).__init__(**kwargs)
        self.headers = None
        self._cookies = None

    def clone(self, owner_instance):
        instance = super(Cookies, self).clone(owner_instance)
        instance.headers = owner_instance.headers
        instance._cookies = None
        return instance

    def __setitem__(self, *args, **kwargs):
        raise TypeError("Cookie modifying allowed only using set() method")

    def __delitem__(self, cookie):
        self.remove(cookie)

    def remove(self, cookie, domain=None, path=None):
        self.set(
            cookie,
            '',
            expires=datetime.datetime(1970, 1, 1),
            domain=domain,
            path=path
        )

    def __getitem__(self, cookie):
        result = self.get(cookie)
        if result is None:
            raise KeyError
        return result

    @property
    def cookies(self):
        if self._cookies is None:
            self._cookies = dict(
                cookie.split('=', 1)
                for cookie in self.headers.get('Cookie', '').split('; ')
                if cookie
            )
        return self._cookies

    def get(self, cookie, default=None, url_decode=False):
        cookie = self.cookies.get(cookie, default)
        if url_decode:
            return urllib.unquote(cookie)
        return cookie

    def set(self, cookie, value, expires=None, domain=None, path=None,
            secure=False, http_only=True, url_encode=False):
        if url_encode:
            value = urllib.quote(value)
        cookie_params = ['%s=%s' % (cookie, value)]
        if domain:
            cookie_params.append("Domain=%s" % domain)
        if path:
            cookie_params.append("Path=%s" % path)
        if isinstance(expires, datetime.datetime):
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=pytz.timezone('GMT'))
            cookie_params.append(
                "Expires=%s" % expires.strftime("%a, %d %b %Y %H:%M:%S %Z"))
        if secure:
            cookie_params.append("Secure")
        if http_only:
            cookie_params.append("HttpOnly")
        self.headers.append('Set-Cookie', '; '.join(cookie_params))
