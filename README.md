marnadi
=======

Yet another WSGI Web Framework, the simplest and fastest ever written.

Hello World
-------
    from marnadi.wsgi import App
    from marnadi import Handler

    application = App()


    @application.route('/')
    @Handler.decorator
    def hello():
        return "Hello World"

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()

More Complex Example
-------

    import re
    from marnadi.wsgi import App
    from marnadi import Handler, Route as r


    class MyHandler(Handler):

        supported_http_methods = ('OPTIONS', 'GET', 'POST')

        # handler of HTTP "GET" requests
        def get(self, receiver, sender=None):
            return 'receiver is %s, sender is %s' % (receiver, sender)


    # handler of HTTP "POST" requests
    # ("GET" and "OPTIONS" already implemented and the rest are restricted
    # by overriding `supported_http_methods`)
    @MyHandler.decorator
    def who_is_foo(foo):
        return "foo is %s" % foo

    routes=(
        ('/', Handler),  # base handler implements only "OPTIONS" method
        r('/foo', who_is_foo, foo='bar'),
        (re.compile(r'/to/(?P<receiver>\w+)/?'), (
            ('', MyHandler),
            (re.compile(r'from/(?P<sender>\w+)$'), MyHandler),
        )),
    )

    application = App(routes=routes)

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()
