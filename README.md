marnadi
=======

Asynchronous web server based on gevent

Example
-------
    import gevent.pywsgi
    import marnadi.handlers
    import marnadi.wsgi


    def main():
        routes = (
            ('/', marnadi.handlers.Handler),
        )
        application = marnadi.wsgi.App(routes)
        gevent.pywsgi.WSGIServer(('', 8000), application).serve_forever()

    if __name__ == '__main__':
        main()