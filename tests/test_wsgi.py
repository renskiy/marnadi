import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from marnadi import Route, Response
from marnadi.errors import HttpError
from marnadi.wsgi import App

_test_handler = Response

_test_handler_seq_routes = (
    Route('a', Response),
    Route('b', Response),
)


class AppTestCase(unittest.TestCase):

    @Response.provider
    def expected_handler(self, *args, **kwargs):
        pass

    @Response.provider
    def unexpected_handler(self, *args, **kwargs):
        pass

    @mock.patch.object(unexpected_handler, 'start')
    @mock.patch.object(expected_handler, 'start')
    def _get_handler_parametrized_test_case(
        self,
        expected,
        unexpected,
        routes,
        requested_path,
        expected_kwargs=None,
    ):
        def side_effect(**kwargs):
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        expected.side_effect = side_effect
        app = App(routes=routes)
        app.get_handler(requested_path)
        self.assertEqual(1, expected.call_count)
        self.assertEqual(0, unexpected.call_count)

    def test_get_handler__expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', self.expected_handler),
            ),
            requested_path='/foo',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler, params=dict(foo='foo')),
            ),
            requested_path='/foo',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__expected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{baz}', self.expected_handler, params=dict(foo='foo')),
            ),
            requested_path='/baz',
            expected_kwargs=dict(foo='foo', baz='baz'),
        )

    def test_get_handler__expected_params_url_route_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}',
                      self.expected_handler, params=dict(foo='baz')),
            ),
            requested_path='/bar',
            expected_kwargs={'foo': 'bar'},
        )

    def test_get_handler__unexpected_error(self):
        with self.assertRaises(HttpError) as context:
            self._get_handler_parametrized_test_case(
                routes=(
                    Route('/foo', self.unexpected_handler),
                ),
                requested_path='/',
            )
        self.assertEqual('404 Not Found', context.exception.status)

    def test_get_handler__unexpected_error2(self):
        with self.assertRaises(HttpError) as context:
            self._get_handler_parametrized_test_case(
                routes=(
                    Route('/', self.unexpected_handler),
                ),
                requested_path='/foo',
            )
        self.assertEqual('404 Not Found', context.exception.status)

    def test_get_handler__expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.unexpected_handler),
                Route('/foo', self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler),
                Route('/', self.unexpected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__expected_unexpected2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler),
                Route('/foo', self.unexpected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__unexpected_expected2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.unexpected_handler),
                Route('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__expected_unexpected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{bar}', self.unexpected_handler),
                Route('/{foo}/', self.expected_handler),
            ),
            requested_path='/foo/',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__unexpected_expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}/', self.expected_handler),
                Route('/{bar}', self.unexpected_handler),
            ),
            requested_path='/foo/',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__expected_unexpected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.unexpected_handler, params=dict(bar='bar')),
                Route('/foo', self.expected_handler, params=dict(foo='foo')),
            ),
            requested_path='/foo',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__unexpected_expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler, params=dict(foo='foo')),
                Route('/', self.unexpected_handler, params=dict(bar='bar')),
            ),
            requested_path='/foo',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__expected_unexpected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{bar}', self.unexpected_handler, params=dict(z2=2)),
                Route('/{foo}/', self.expected_handler, params=dict(z1=1)),
            ),
            requested_path='/foo/',
            expected_kwargs=dict(foo='foo', z1=1),
        )

    def test_get_handler__unexpected_expected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}/', self.expected_handler, params=dict(z1=1)),
                Route('/{bar}', self.unexpected_handler, params=dict(z2=2)),
            ),
            requested_path='/foo/',
            expected_kwargs=dict(foo='foo', z1=1),
        )

    def test_get_handler__nested_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', (
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__nested_expected_params_url2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', (
                    Route('/{bar}', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler__nested_expected_params_url2_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', (
                    Route('/{foo}', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='bar'),
        )

    def test_get_handler__nested_expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler),
                ), params=dict(foo='foo')),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__nested_expected_params_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler,
                          params=dict(bar='bar')),
                ), params=dict(foo='foo')),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler__nested_expected_params_route2_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler,
                          params=dict(foo='bar')),
                ), params=dict(foo='foo')),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='bar'),
        )

    def test_get_handler__nested_expected_params_url2_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', (
                    Route('/{bar}', self.expected_handler,
                          params=dict(y='y')),
                ), params=dict(x='x')),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo', bar='bar', x='x', y='y'),
        )

    def test_get_handler__nested_expected_params_url2_route2_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', (
                    Route('/{bar}', self.expected_handler,
                          params=dict(foo='baz')),
                ), params=dict(bar='bar')),
            ),
            requested_path='/foo/baz',
            expected_kwargs=dict(foo='baz', bar='baz'),
        )

    def test_get_handler__nested_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('', self.unexpected_handler),
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler),
                    Route('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_unexpected_expected_half(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.unexpected_handler),
                    Route('', self.expected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_expected_unexpected_half(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('', self.expected_handler),
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested2_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/baz', self.expected_handler),
                )),
                Route('/foo', (
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested2_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.unexpected_handler),
                )),
                Route('/foo', (
                    Route('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested2_unexpected_expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler),
                )),
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested2_expected_unexpected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler),
                )),
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested2_unexpected_expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
                Route('/foo', (
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
            ),
            requested_path='/foo/baz',
            expected_kwargs=dict(f2=2),
        )

    def test_get_handler__nested2_expected_unexpected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
                Route('/foo', (
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
            ),
            requested_path='/foo/baz',
            expected_kwargs=dict(f2=2),
        )

    def test_get_handler__nested2_unexpected_expected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2),
        )

    def test_get_handler__nested2_expected_unexpected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2),
        )

    def test_get_handler__nested2_unexpected_expected_params_url2_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', (
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                )),
                Route('/foo/{kwarg2}', (
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                )),
            ),
            requested_path='/foo/kwarg/baz/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, baz='baz'),
        )

    def test_get_handler__nested2_expected_unexpected_params_url2_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', (
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                )),
                Route('/foo/{kwarg1}', (
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                )),
            ),
            requested_path='/foo/kwarg/baz/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, baz='baz'),
        )

    def test_get_handler__nested2_unexpected_expected_params_url_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, z2='z2'),
        )

    def test_get_handler__nested2_expected_unexpected_params_url_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', (
                    Route('/baz', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
                Route('/foo/{kwarg1}', (
                    Route('/bar', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, z2='z2'),
        )

    def test_get_handler__nested2_unexpected_expected_params_url2_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', (
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
                Route('/foo/{kwarg2}', (
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
            ),
            requested_path='/foo/kwarg/baz/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, baz='baz', z2='z2'),
        )

    def test_get_handler__nested2_expected_unexpected_params_url2_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', (
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
                Route('/foo/{kwarg1}', (
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
            ),
            requested_path='/foo/kwarg/baz/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2, baz='baz', z2='z2'),
        )

    def test_get_handler__nested2_expected_unexpected_half_error(self):
        with self.assertRaises(HttpError) as context:
            self._get_handler_parametrized_test_case(
                routes=(
                    Route('/foo', (
                        Route('/baz', self.expected_handler),
                    )),
                    Route('/foo', (
                        Route('/bar', self.unexpected_handler),
                    )),
                ),
                requested_path='/foo',
            )
        self.assertEqual('404 Not Found', context.exception.status)

    def test_get_handler__nested2_unexpected_expected_half_error(self):
        with self.assertRaises(HttpError) as context:
            self._get_handler_parametrized_test_case(
                routes=(
                    Route('/foo', (
                        Route('/bar', self.unexpected_handler),
                    )),
                    Route('/foo', (
                        Route('/baz', self.expected_handler),
                    )),
                ),
                requested_path='/foo',
            )
        self.assertEqual('404 Not Found', context.exception.status)

    def test_compile_routes__empty(self):
        app = App()
        self.assertListEqual([], app.routes)

    def test_compile_routes(self):
        route = Route('/', _test_handler)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)

    def test_compile_routes__routes(self):
        route = Route('/', _test_handler_seq_routes)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)
        route_a, route_b = route.handler
        self.assertIsInstance(route_a, Route)
        self.assertIsInstance(route_b, Route)
        self.assertEqual(_test_handler, route_a.handler)
        self.assertEqual(_test_handler, route_b.handler)

    def test_compile_routes__lazy_handler(self):
        route = Route('/', '%s._test_handler' % __name__)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)

    def test_compile_routes__lazy_routes(self):
        route = Route('/', '%s._test_handler_seq_routes' % __name__)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)
        route_a, route_b = route.handler
        self.assertIsInstance(route_a, Route)
        self.assertIsInstance(route_b, Route)
        self.assertEqual(_test_handler, route_a.handler)
        self.assertEqual(_test_handler, route_b.handler)

    def test_compile_routes__typeerror(self):
        wrong_handler = 123
        routes = (
            Route('path', wrong_handler),
        )
        with self.assertRaises(TypeError) as context:
            App(routes=routes)
        self.assertIn('subclass of Handler', str(context.exception))

    @mock.patch.object(Response, 'start')
    def test_route(self, mocked):
        def side_effect(**kwargs):
            self.assertDictEqual(
                dict(kwarg='kwarg', foo='foo'),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        app.route('/{foo}', params=dict(kwarg='kwarg'))(Response)
        app.get_handler('/foo')
        self.assertEqual(1, mocked.call_count)

    @mock.patch.object(Response, 'start')
    def test_route__routes(self, mocked):
        def side_effect(**kwargs):
            self.assertDictEqual(
                dict(kwarg1='kwarg1', kwarg2='kwarg2', kwarg=2, bar='bar',
                     foo='foo'),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        routes = (
            Route('/{bar}', Response, params=dict(kwarg2='kwarg2', kwarg=2)),
        )
        app.route('/{foo}', params=dict(kwarg1='kwarg1', kwarg=1))(routes)
        app.get_handler('/foo/bar')
        self.assertEqual(1, mocked.call_count)
