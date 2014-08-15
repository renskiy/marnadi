marnadi
=======

Yet another WSGI Web Framework, the simplest and fastest ever written.

Does not have any dependency. Works both with **Python 2** and **Python 3**.

Hello World
-------
```python
from marnadi.wsgi import App
from marnadi import Response

application = App()


@application.route('/')
@Response.provider
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
from marnadi import Response, Route


class MyResponse(Response):

    # HTTP GET request handler
    def get(self, foo, bar=None):
        return 'foo is {foo}, bar is {bar}'.format(foo=foo, bar=bar)

routes=(
    Route(re.compile(r'/(?P<foo>\w+)/'), (
        Route('', MyResponse),
        Route(re.compile(r'(?P<bar>\w+)/$'), MyResponse),
    )),
)

application = App(routes=routes)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    make_server('', 8000, application).serve_forever()
```
