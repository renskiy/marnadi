import unittest

from marnadi import Response
from marnadi.helpers import Route
from marnadi.wsgi import Request, App

handler_function = Response.get(lambda: 'foo')

handler_class = type('MyHandler', (Response, ), dict(
    get=lambda *args: 'hello'
))


class HandlerTestCase(unittest.TestCase):

    def handler_parametrized_test_case(
        self,
        routes,
        environ,
        expected_result,
        expected_status="200 OK",
        expected_headers=None,
        unexpected_headers=None,
    ):
        def start_response(status, headers):
            self.assertEqual(expected_status, status)
            for header in expected_headers or ():
                self.assertIn(header, headers)
            for header in unexpected_headers or ():
                self.assertNotIn(header, headers)

        app = App(routes=routes)
        actual_result = b''.join(app(environ, start_response))
        self.assertEqual(expected_result, actual_result)

    def test_handler_as_function(self):
        routes = (
            Route('/', handler_function),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_result=b'foo',
            expected_headers=(
                ('Content-Length', '3'),
            ),
        )

    def test_handler_as_class(self):
        routes = (
            Route('/', handler_class),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_handler_as_lazy_function(self):
        routes = (
            Route('/', '%s.handler_function' % __name__),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_result=b'foo',
            expected_headers=(
                ('Content-Length', '3'),
            ),
        )

    def test_handler_as_lazy_class(self):
        routes = (
            Route('/', '%s.handler_class' % __name__),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_handler_not_supported_method(self):
        routes = (
            Route('/', Response),
        )
        environ = Request(dict(
            REQUEST_METHOD='NOT_SUPPORTED_METHOD',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_status='501 Not Implemented',
            expected_result=b'501 Not Implemented',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Allow', 'OPTIONS'),
            ),
        )

    def test_handler_not_allowed_method(self):
        routes = (
            Route('/', Response),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self.handler_parametrized_test_case(
            routes=routes,
            environ=environ,
            expected_status='405 Method Not Allowed',
            expected_result=b'405 Method Not Allowed',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Allow', 'OPTIONS'),
            ),
        )
