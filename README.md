marnadi
=======

Yet another WSGI Web Framework, the simplest and fastest ever written

Hello World
-------
    from marnadi import App, Handler

    application = App()


    @application.route('/')
    @Handler.decorator
    def hello():
        return "Hello World"
    )

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()

More Complex Example
-------

    import re
    from marnadi import Header, Handler, Route as r


    class MyHandler(Handler):

        SUPPORTED_HTTP_METHODS = ('OPTIONS', 'GET', 'POST')

        # handler of HTTP "GET" requests
        def get(self, receiver, sender=None):
            return 'receiver is %s, sender is %s' % (receiver, sender)


    # handler of HTTP "POST" requests
    # ("GET" and "OPTIONS" already implemented and the rest are restricted
    # by overriding SUPPORTED_HTTP_METHODS)
    @MyHandler.decorator
    def foo(foo):
        return "foo is %s" % foo

    routes=(
        r('/foo', foo, foo='bar'),
        (re.compile(r'/to/(?P<receiver>\w+)/?'), (
            ('', JsonHandler),
            (re.compile(r'from/(?P<sender>\w+)$'), JsonHandler),
        )),
    )

    application = App(routes=routes)

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()
