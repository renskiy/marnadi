import io
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from marnadi import Response, Route
from marnadi.wsgi import Request, App

handler_function = Response.get(lambda: 'foo')

handler_class = type('MyHandler', (Response, ), dict(
    get=lambda *args: 'hello'
))


class ResponseTestCase(unittest.TestCase):

    def _handle_request(
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

    def test_as_function(self):
        routes = (
            Route('/', handler_function),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'foo',
            expected_headers=(
                ('Content-Length', '3'),
            ),
        )

    def test_as_class(self):
        routes = (
            Route('/', handler_class),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_as_lazy_function(self):
        routes = (
            Route('/', '%s.handler_function' % __name__),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'foo',
            expected_headers=(
                ('Content-Length', '3'),
            ),
        )

    def test_as_lazy_class(self):
        routes = (
            Route('/', '%s.handler_class' % __name__),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_not_supported_method(self):
        routes = (
            Route('/', Response),
        )
        environ = Request(dict(
            REQUEST_METHOD='NOT_SUPPORTED_METHOD',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_status='501 Not Implemented',
            expected_result=b'501 Not Implemented',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Allow', 'OPTIONS'),
                ('Content-Length', '19'),
            ),
        )

    def test_not_allowed_method(self):
        routes = (
            Route('/', Response),
        )
        environ = Request(dict(
            REQUEST_METHOD='GET',
            PATH_INFO='/',
        ))
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_status='405 Method Not Allowed',
            expected_result=b'405 Method Not Allowed',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Allow', 'OPTIONS'),
                ('Content-Length', '22'),
            ),
        )

    def test_post_application_json(self):
        routes = (
            Route('/', type('', (Response, ), dict(
                post=lambda this: this.request.data,
            ))),
        )
        environ = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/',
            'wsgi.input': io.BytesIO(b'"hello"'),
            'CONTENT_LENGTH': '7',
            'CONTENT_TYPE': 'application/json',
        })
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_post_broken_application_json(self):
        routes = (
            Route('/', type('', (Response, ), dict(
                post=lambda this: this.request.data,
            ))),
        )
        environ = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/',
            'wsgi.input': io.BytesIO(b'"hello'),
            'CONTENT_LENGTH': '6',
            'CONTENT_TYPE': 'application/json',
        })
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_status='400 Bad Request',
            expected_result=b'400 Bad Request',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', '15'),
            ),
        )

    def test_post_application_x_www_form_urlencoded(self):
        routes = (
            Route('/', type('', (Response, ), dict(
                post=lambda this: this.request.data['hello'],
            ))),
        )
        environ = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/',
            'wsgi.input': io.BytesIO(b'hello=world'),
            'CONTENT_LENGTH': '11',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        })
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b"world",
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_post(self, content_type=''):
        routes = (
            Route('/', type('', (Response, ), dict(
                post=lambda this: str(this.request.data),
            ))),
        )
        environ = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/',
            'wsgi.input': io.BytesIO(b'hello'),
            'CONTENT_LENGTH': '5',
            'CONTENT_TYPE': content_type,
        })
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_result=b'hello',
            expected_headers=(
                ('Content-Length', '5'),
            ),
        )

    def test_post_text_plain(self):
        self.test_post('text/plain')

    def test_post_broken_unicode(self):
        routes = (
            Route('/', type('', (Response, ), dict(
                post=lambda this: this.request.data,
            ))),
        )
        environ = Request({
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/',
            'wsgi.input': io.BytesIO(b'\xd0'),
            'CONTENT_LENGTH': '1',
        })
        self._handle_request(
            routes=routes,
            environ=environ,
            expected_status='400 Bad Request',
            expected_result=b'400 Bad Request',
            expected_headers=(
                ('Content-Type', 'text/plain; charset=utf-8'),
                ('Content-Length', '15'),
            ),
        )
