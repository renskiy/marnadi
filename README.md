marnadi
=======

Asynchronous web server based on gevent

Example
-------
    import re
    import gevent.pywsgi
    from marnadi import handlers, wsgi

    import myproject

    routes = (
        ('/', handlers.Handler),
        (re.compile(r'^/hello/(?P<dude>\w+)'), (
            ('', handlers.Handler),
            (re.compile(r'^/from/(?P<friend>\w+)$'), MyHandler),
        )),
        ('/myproject', myproject.routes),
    )


    class MyHandler(handlers.Handler):

        def get(self, **kwargs):
            result = '%(dude)s got hello from %(friend)s' % kwargs
            self.headers.extend(
                ('Content-Type', 'text/plain'),
                ('Content-Length', len(result)),
            )
            yield result


    def main():
        application = wsgi.App(routes)
        gevent.pywsgi.WSGIServer(('', 8000), application).serve_forever()

    if __name__ == '__main__':
        main()