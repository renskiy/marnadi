from marnadi.http.descriptors import Descriptor


class Cookies(Descriptor):
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