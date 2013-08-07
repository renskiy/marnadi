marnadi
=======

Yet another Web Framework with Blackjack and something you will really like

Example
-------
    from marnadi import handlers, wsgi


    class MyHandler(handlers.Handler):

        def get(self):
            return 'Hello World'

    application = wsgi.App(
        routes=('/', MyHandler),
    )

    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()