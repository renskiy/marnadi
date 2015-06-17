marnadi
=======

.. image:: https://travis-ci.org/renskiy/marnadi.svg?branch=master
    :target: https://travis-ci.org/renskiy/marnadi

Yet another WSGI Web Framework, the simplest and fastest ever written.

Has no dependencies. Works both with **Python 2** and **Python 3**.

Features
--------
* Support both of functional and object-oriented programming styles
* Dynamic routes, e.g. "/path/{param}/"
* Headers, query, data, cookies descriptors
* Rich extending abilities

Installation
------------
Simply execute following line::

    pip install marnadi

"Hello World"
-------------
Run this script and open http://localhost:8000/ on your browser:

.. code-block:: python

    from marnadi.response import Response
    from marnadi.wsgi import App

    application = App()
    
    
    @application.route('/')
    @Response.get
    def main_page():
        return 'This is main page'
    
    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()

More complex example
--------------------
Script below additionally will respond to http://localhost:8000/foo/bar/ and http://localhost:8000/foo/ requests:

.. code-block:: python

    from marnadi.response import Response
    from marnadi.route import Route
    from marnadi.wsgi import App


    class MainPageResponse(Response):

        def get(self):
            return 'This is main page'
    
    
    class FooBarResponse(Response):
    
        def get(self, foo, bar=None):
            return 'foo is {foo}, bar is {bar}'.format(foo=foo, bar=bar)
    
    routes=(
        Route('/', MainPageResponse),
        Route('/{foo}/', FooBarResponse, routes=(
            Route('{bar}/', FooBarResponse),
        )),
    )
    
    application = App(routes=routes)
    
    if __name__ == '__main__':
        from wsgiref.simple_server import make_server
        make_server('', 8000, application).serve_forever()
