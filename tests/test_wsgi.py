import mock
import re
import unittest

from marnadi import Route, Response
from marnadi.errors import HttpError
from marnadi.wsgi import App

_test_handler = Response

_test_handler_seq_routes = (
    Route('a', Response),
    Route('b', Response),
)


class AppTestCase(unittest.TestCase):

    @mock.patch.object(Response, 'start')
    def _get_handler_args_parametrized_test_case(
        self,
        mocked,
        handler_path,
        requested_path='/foo/bar',
        nested_handler_path=None,
        expected_kwargs=None,
    ):
        def side_effect(**kwargs):
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        mocked.side_effect = side_effect
        routes = (
            Route(handler_path, nested_handler_path is None and Response or (
                Route(nested_handler_path, Response),
            )),
        )
        app = App(routes=routes)
        app.get_handler(requested_path)
        self.assertEqual(1, mocked.call_count)

    def test_get_handler_args__no_args(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo/bar',
        )

    def test_get_handler_args__kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)/bar'),
            expected_kwargs=dict(key_foo='foo'),
        )

    def test_get_handler_args__kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)/(?P<key_bar>\w+)'),
            expected_kwargs=dict(key_foo='foo', key_bar='bar'),
        )

    def test_get_handler_args__nested_const_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo',
            nested_handler_path=re.compile(r'/(?P<key_bar>\w+)'),
            expected_kwargs=dict(key_bar='bar'),
        )

    def test_get_handler_args__nested_kwarg_const(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)'),
            nested_handler_path='/bar',
            expected_kwargs=dict(key_foo='foo'),
        )

    def test_get_handler_args__nested_kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)'),
            nested_handler_path=re.compile(r'/(?P<key_bar>\w+)'),
            expected_kwargs=dict(key_foo='foo', key_bar='bar'),
        )

    def test_get_handler__handler_not_found(self):
        app = App()
        with self.assertRaises(HttpError) as context:
            app.get_handler('unknown_path')
        error = context.exception
        self.assertEqual('404 Not Found', error.status)

    @Response.decorator
    def expected_handler(self, *args, **kwargs):
        pass

    @Response.decorator
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

    def test_get_handler__expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler),
                Route('/foo', self.unexpected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.unexpected_handler),
                Route('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/'), self.expected_handler),
                Route(re.compile(r'/foo'), self.unexpected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), self.unexpected_handler),
                Route(re.compile(r'/'), self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_unexpected_expected_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'),
                      self.unexpected_handler, bar='baz'),
                Route(re.compile(r'/'), self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.unexpected_handler),
                Route('/foo', self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler),
                Route('/', self.unexpected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_regexp_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/'), self.unexpected_handler),
                Route(re.compile(r'/foo'), self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_regexp_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), self.expected_handler),
                Route(re.compile(r'/'), self.unexpected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.unexpected_handler),
                    Route('', self.expected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('', self.expected_handler),
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_regexp_foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route('/bar', self.unexpected_handler),
                    Route('', self.expected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_regexp_foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route('', self.expected_handler),
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foobar_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('', self.unexpected_handler),
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_foobar_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', (
                    Route('/bar', self.expected_handler),
                    Route('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_regexp_foobar_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route('', self.unexpected_handler),
                    Route(re.compile(r'/bar'), self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_regexp_foobar_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route(re.compile(r'/bar'), self.expected_handler),
                    Route('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_foobaz_expected_unexpected(self):
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

    def test_get_handler__nested_foobaz_unexpected_expected(self):
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

    def test_get_handler__nested_foobaz_unexpected_expected_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo/(?P<kwarg1>kwarg)'), (
                    Route('/bar', self.unexpected_handler),
                )),
                Route(re.compile(r'/foo/(?P<kwarg2>kwarg)'), (
                    Route('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested_regexp_foobaz_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route(re.compile(r'/baz'), self.expected_handler),
                )),
                Route(re.compile(r'/foo'), (
                    Route(re.compile(r'/bar'), self.unexpected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested_regexp_foobaz_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'), (
                    Route(re.compile(r'/bar'), self.unexpected_handler),
                )),
                Route(re.compile(r'/foo'), (
                    Route(re.compile(r'/baz'), self.expected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler_predefined(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler_predefined__kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler, foo='foo', bar='bar'),
            ),
            requested_path='/',
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler_predefined__route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler_predefined__regexp_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(
                    re.compile(r'/(?P<baz>baz)'),
                    self.expected_handler, foo='foo', bar='bar',
                ),
            ),
            requested_path='/baz',
            expected_kwargs=dict(foo='foo', bar='bar', baz='baz'),
        )

    def test_get_handler_predefined__regexp_kwargs_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(?P<foo>bar)'),
                      self.expected_handler, foo='baz'),
            ),
            requested_path='/bar',
            expected_kwargs={'foo': 'bar'},
        )

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
                dict(kwarg='kwarg'),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        app.route('/', kwarg='kwarg')(Response)
        app.get_handler('/')
        self.assertEqual(1, mocked.call_count)

    @mock.patch.object(Response, 'start')
    def test_route__routes(self, mocked):
        def side_effect(**kwargs):
            self.assertDictEqual(
                dict(kwarg1='kwarg1', kwarg2='kwarg2', kwarg=2),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        routes = (
            Route('path', Response, kwarg2='kwarg2', kwarg=2),
        )
        app.route('/', kwarg1='kwarg1', kwarg=1)(routes)
        app.get_handler('/path')
        self.assertEqual(1, mocked.call_count)
