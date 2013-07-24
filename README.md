marnadi
=======

Asynchronous web server based on gevent

Example
-------
    # this file can be attached to any WSGI-compatible server (e.g. uwsgi)
    # or even executed from command line (require 'gevent')

    import re
    from marnadi import handlers, wsgi


    class MyHandler(handlers.Handler):

        def get(self):
            return 'Hello World'


    application = wsgi.App(
        ('/', MyHandler),
    )

    if __name__ == '__main__':
        import gevent.pywsgi
        gevent.pywsgi.WSGIServer(('', 8000), application).serve_forever()