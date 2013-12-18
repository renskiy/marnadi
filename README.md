marnadi
=======

Yet another WSGI Web Framework, the simplest and fastest ever written

Hello World
-------
    from marnadi import wsgi


    @wsgi.Handler.decorator
    def hello():
        return "Hello World"

    routes=(
        ('/', hello),
    )

    application = wsgi.App(routes=routes)

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()

More Complex Example
-------

    import json
    import re
    from marnadi import wsgi, Route


    class JsonHandler(wsgi.Handler):

        SUPPORTED_HTTP_METHODS = ('OPTIONS', 'GET', 'POST')

        headers = descriptors.Headers(
            ('Content-Type', 'application/json; charset=utf-8'),
        )

        def __call__(self, *args, **kwargs):
            result = super(JsonHandler, self).__call__(*args, **kwargs)
            return json.dumps(result)

        def get(self, receiver, sender=None):
            return {'Hello':  receiver, 'from': sender}


    @JsonHandler.decorator
    def foo(foo, bar=None):  # will be called only on HTTP "POST" request
        return {'foo': foo, 'bar': bar}

    @wsgi.Handler.decorator
    def http_stream(*args):
        for arg in args:
            yield arg

    hello_routes = (
        ('', JsonHandler),
        (re.compile(r'from/(?P<sender>\w+)$'), JsonHandler),
    )

    routes=(
        ('/', wsgi.Handler),  # HTTP 405 Method Not Allowed
        Route(re.compile(r'/foo/(?P<foo>\w+')$'), foo, bar='bar'),
        ('/http_stream', http_stream, 1, 2, 3),
        (re.compile(r'/hello/(?P<receiver>\w+)/?'), hello_routes),
        ('/lazy', 'path.to.handler'),
        ('/nested', 'path.to.subroutes')
    )

    application = wsgi.App(routes=routes)

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()
