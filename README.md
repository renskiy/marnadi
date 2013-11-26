marnadi
=======

Yet another WSGI Web Server, the simplest and fastest ever written

Hello World
-------
    from marnadi import wsgi


    @wsgi.Handler
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
    from marnadi import wsgi, Lazy


    class JsonHandler(wsgi.Handler):

        SUPPORTED_HTTP_METHODS = ('OPTIONS', 'GET')

        headers = descriptors.Headers(
            ('Content-Type', 'application/json; charset=utf-8'),
        )

        def __call__(self, *args, **kwargs):
            result = super(JsonHandler, self).__call__(*args, **kwargs)
            return json.dumps(result)

        def get(self, receiver, sender=None):
            return {'Hello':  receiver, 'from': sender}


    @JsonHandler
    def foo(bar):
        return {'foo': bar}

    hello_routes = (
        ('', JsonHandler),
        (re.compile(r'from/(?P<sender>\w+)$'), JsonHandler),
    )

    routes=(
        ('/', wsgi.Handler),  # HTTP 405 Method Not Allowed
        (re.compile(r'/foo/(?P<bar>\w+')$'), foo),
        (re.compile(r'/hello/(?P<receiver>\w+)/?'), hello_routes),
        ('/lazy', Lazy('path.to.handler')),
        ('/nested', Lazy('path.to.subroutes'))
    )

    application = wsgi.App(routes=routes)

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()