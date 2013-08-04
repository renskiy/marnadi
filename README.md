marnadi
=======

Web-framework with Black Jack and some thing you will like

Example
-------
    from marnadi import handlers, wsgi


    class MyHandler(handlers.Handler):

        def get(self):
            return 'Hello World'

    application = wsgi.App(
        ('/', MyHandler),
    )

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()