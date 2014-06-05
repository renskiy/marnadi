marnadi
=======

Yet another WSGI Web Framework, the simplest and fastest ever written.

Hello World
-------
```python
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
```

More Complex Example
-------
```python
import re
from marnadi.wsgi import App
from marnadi import Handler, Route as r


class MyHandler(Handler):

    supported_http_methods = ('OPTIONS', 'GET', 'POST')

    # "GET" request handler
    def get(self, receiver, sender=None):
        return 'receiver is %s, sender is %s' % (receiver, sender)


# "POST" request handler
# (that is because `get` and `options` are defined in MyHandler and Handler,
# thus and because of MyHandler's `supported_http_methods` it will handle
# only "POST" requests)
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
```
