import mock
import re
import unittest

from marnadi import Route, Response
from marnadi.errors import HttpError
from marnadi.wsgi import Request, App

_test_handler = Response

_test_handler_seq = (
    ('a', Response),
    ('b', Response),
)

_test_handler_seq_routes = (
    Route('a', Response),
    Route('b', Response),
)


class RequestTestCase(unittest.TestCase):

    def test_attribute_getter(self):
        environ = {
            'wsgi.input': 'input',
        }
        request = Request(environ)

        self.assertEqual(request.input, 'input')
        self.assertEqual(request['wsgi.input'], 'input')

        with self.assertRaises(AttributeError):
            getattr(request, 'unknown_wsgi_key')
        self.assertNotIn('unknown_wsgi_key', request)


class AppTestCase(unittest.TestCase):

    @mock.patch.object(Response, 'handle')
    def _get_handler_args_parametrized_test_case(
        self,
        mocked,
        handler_path,
        requested_path='/foo/bar',
        nested_handler_path=None,
        expected_args=None,
        expected_kwargs=None,
    ):
        def side_effect(*args, **kwargs):
            self.assertListEqual(expected_args or [], list(args))
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        mocked.side_effect = side_effect
        routes = (
            (handler_path, nested_handler_path is None and Response or (
                (nested_handler_path, Response),
            )),
        )
        app = App(routes=routes)
        app.get_handler(requested_path)
        self.assertEqual(1, mocked.call_count)

    def test_get_handler_args__no_args(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo/bar',
        )

    def test_get_handler_args__arg_kwarg_collision(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(foo)/(?P<key_foo>foo)'),
            requested_path='/foo/foo',
            expected_args=['foo'],
            expected_kwargs={'key_foo': 'foo'},
        )

    def test_get_handler_args__arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/bar'),
            expected_args=['foo'],
        )

    def test_get_handler_args__arg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/(\w+)'),
            expected_args=['foo', 'bar'],
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

    def test_get_handler_args__arg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/(?P<key_bar>\w+)'),
            expected_args=['foo'],
            expected_kwargs=dict(key_bar='bar'),
        )

    def test_get_handler_args__kwarg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)/(\w+)'),
            expected_args=['bar'],
            expected_kwargs=dict(key_foo='foo'),
        )

    def test_get_handler_args__nested_const_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo',
            nested_handler_path=re.compile(r'/(\w+)'),
            expected_args=['bar'],
        )

    def test_get_handler_args__nested_arg_const(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)'),
            nested_handler_path='/bar',
            expected_args=['foo'],
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

    def test_get_handler_args__nested_arg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)'),
            nested_handler_path=re.compile(r'/(\w+)'),
            expected_args=['foo', 'bar'],
        )

    def test_get_handler_args__nested_kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)'),
            nested_handler_path=re.compile(r'/(?P<key_bar>\w+)'),
            expected_kwargs=dict(key_foo='foo', key_bar='bar'),
        )

    def test_get_handler_args__nested_arg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)'),
            nested_handler_path=re.compile(r'/(?P<key_bar>\w+)'),
            expected_args=['foo'],
            expected_kwargs=dict(key_bar='bar'),
        )

    def test_get_handler_args__nested_kwarg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<key_foo>\w+)'),
            nested_handler_path=re.compile(r'/(\w+)'),
            expected_args=['bar'],
            expected_kwargs=dict(key_foo='foo'),
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

    @mock.patch.object(unexpected_handler, 'handle')
    @mock.patch.object(expected_handler, 'handle')
    def _get_handler_parametrized_test_case(
        self,
        expected,
        unexpected,
        routes,
        requested_path,
        expected_args=None,
        expected_kwargs=None,
    ):
        def side_effect(*args, **kwargs):
            self.assertListEqual(expected_args or [], list(args))
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        expected.side_effect = side_effect
        app = App(routes=routes)
        app.get_handler(requested_path)
        self.assertEqual(1, expected.call_count)
        self.assertEqual(0, unexpected.call_count)

    def test_get_handler__expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/', self.expected_handler),
                ('/foo', self.unexpected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', self.unexpected_handler),
                ('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/'), self.expected_handler),
                (re.compile(r'/foo'), self.unexpected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), self.unexpected_handler),
                (re.compile(r'/'), self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__regexp_unexpected_expected_args_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/foo'),
                      self.unexpected_handler, 'foo', bar='baz'),
                (re.compile(r'/'), self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler__foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/', self.unexpected_handler),
                ('/foo', self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', self.expected_handler),
                ('/', self.unexpected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_regexp_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/'), self.unexpected_handler),
                (re.compile(r'/foo'), self.expected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__foo_regexp_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), self.expected_handler),
                (re.compile(r'/'), self.unexpected_handler),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('/bar', self.unexpected_handler),
                    ('', self.expected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('', self.expected_handler),
                    ('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_regexp_foo_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    ('/bar', self.unexpected_handler),
                    ('', self.expected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_regexp_foo_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    ('', self.expected_handler),
                    ('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested_foobar_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('', self.unexpected_handler),
                    ('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_foobar_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('/bar', self.expected_handler),
                    ('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_regexp_foobar_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    ('', self.unexpected_handler),
                    (re.compile(r'/bar'), self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_regexp_foobar_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    (re.compile(r'/bar'), self.expected_handler),
                    ('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_foobaz_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('/baz', self.expected_handler),
                )),
                ('/foo', (
                    ('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested_foobaz_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/foo', (
                    ('/bar', self.unexpected_handler),
                )),
                ('/foo', (
                    ('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested_foobaz_unexpected_expected_args_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/(foo)/(?P<kwarg1>kwarg)'), (
                    ('/bar', self.unexpected_handler),
                )),
                (re.compile(r'/(foo)/(?P<kwarg2>kwarg)'), (
                    ('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_args=['foo'],
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested_regexp_foobaz_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    (re.compile(r'/baz'), self.expected_handler),
                )),
                (re.compile(r'/foo'), (
                    (re.compile(r'/bar'), self.unexpected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested_regexp_foobaz_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/foo'), (
                    (re.compile(r'/bar'), self.unexpected_handler),
                )),
                (re.compile(r'/foo'), (
                    (re.compile(r'/baz'), self.expected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler_predefined(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler_predefined__args(self):
        self._get_handler_parametrized_test_case(
            routes=(
                ('/', self.expected_handler, 'foo', 'bar'),
            ),
            requested_path='/',
            expected_args=['foo', 'bar'],
        )

    def test_get_handler_predefined__route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler),
            ),
            requested_path='/',
        )

    def test_get_handler_predefined__route_args(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler, 'foo', 'bar'),
            ),
            requested_path='/',
            expected_args=['foo', 'bar'],
        )

    def test_get_handler_predefined__route_args_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/', self.expected_handler, 'foo', 'bar', key_baz='baz'),
            ),
            requested_path='/',
            expected_args=['foo', 'bar'],
            expected_kwargs={'key_baz': 'baz'},
        )

    def test_get_handler_predefined__regexp_args(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/(baz)'), self.expected_handler, 'foo', 'bar'),
            ),
            requested_path='/baz',
            expected_args=['foo', 'bar', 'baz'],
        )

    def test_get_handler_predefined__regexp_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(baz)'), self.expected_handler),
            ),
            requested_path='/baz',
            expected_args=['baz'],
        )

    def test_get_handler_predefined__regexp_route_args(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(baz)'),
                      self.expected_handler, 'foo', 'bar'),
            ),
            requested_path='/baz',
            expected_args=['foo', 'bar', 'baz'],
        )

    def test_get_handler_predefined__regexp_route_args_kwargs(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(baz)'),
                      self.expected_handler, 'foo', 'bar', key_baz='baz'),
            ),
            requested_path='/baz',
            expected_args=['foo', 'bar', 'baz'],
            expected_kwargs={'key_baz': 'baz'},
        )

    def test_get_handler_predefined__regexp_route_kwargs_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(?P<key_baz>bar)'),
                      self.expected_handler, key_baz='baz'),
            ),
            requested_path='/bar',
            expected_kwargs={'key_baz': 'bar'},
        )

    def test_get_handler_predefined__regexp_route_complex(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(?P<key_foo>foo)/(bar)'),
                      self.expected_handler, 'foo', key_baz='baz'),
            ),
            requested_path='/foo/bar',
            expected_args=['foo', 'bar'],
            expected_kwargs={'key_baz': 'baz', 'key_foo': 'foo'},
        )

    @unittest.skip(
        "The order of args received by handler is wrong "
        "due to inability to determine correct one"
    )
    def test_get_handler__non_trivial_situation(self):
        self._get_handler_parametrized_test_case(
            routes=(
                (re.compile(r'/(foo)/(bar)/(?P<key_foo>foo)'),
                    self.expected_handler),
            ),
            requested_path='/foo/bar/foo',
            expected_args=['foo', 'bar'],  # actual is ['bar', 'foo']
            expected_kwargs={'key_foo': 'foo'},
        )

    def test_compile_routes(self):
        app = App()
        self.assertListEqual([], app.routes)

    def test_compile_routes__tuple(self):
        app = App(routes=(
            ('/', _test_handler),
        ))
        self.assertEqual(1, len(app.routes))
        route = app.routes[0]
        self.assertIsInstance(route, Route)
        self.assertEqual(_test_handler, route.handler)

    def test_compile_routes__tuple_lazy_handler(self):
        app = App(routes=(
            ('/', '%s._test_handler' % __name__),
        ))
        self.assertEqual(1, len(app.routes))
        route = app.routes[0]
        self.assertIsInstance(route, Route)
        self.assertTrue(issubclass(route.handler, Response))

    def test_compile_routes__tuple_lazy_seq(self):
        app = App(routes=(
            ('/', '%s._test_handler_seq' % __name__),
        ))
        self.assertEqual(1, len(app.routes))
        root_route = app.routes[0]
        self.assertEqual(2, len(root_route.handler))
        route_a, route_b = root_route.handler
        self.assertIsInstance(route_a, Route)
        self.assertIsInstance(route_b, Route)
        self.assertEqual(_test_handler, route_a.handler)
        self.assertEqual(_test_handler, route_b.handler)

    def test_compile_routes__tuple_lazy_seq_routes(self):
        app = App(routes=(
            ('/', '%s._test_handler_seq_routes' % __name__),
        ))
        self.assertEqual(1, len(app.routes))
        root_route = app.routes[0]
        self.assertEqual(2, len(root_route.handler))
        route_a, route_b = root_route.handler
        self.assertIsInstance(route_a, Route)
        self.assertIsInstance(route_b, Route)
        self.assertEqual(_test_handler, route_a.handler)
        self.assertEqual(_test_handler, route_b.handler)

    def test_compile_routes__route(self):
        route = Route('/', _test_handler)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)

    def test_compile_routes__route_lazy_handler(self):
        route = Route('/', '%s._test_handler' % __name__)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)

    def test_compile_routes__route_lazy_seq(self):
        route = Route('/', '%s._test_handler_seq' % __name__)
        app = App(routes=(route, ))
        self.assertListEqual([route], app.routes)
        route_a, route_b = route.handler
        self.assertIsInstance(route_a, Route)
        self.assertIsInstance(route_b, Route)
        self.assertEqual(_test_handler, route_a.handler)
        self.assertEqual(_test_handler, route_b.handler)

    def test_compile_routes__route_lazy_seq_routes(self):
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
            ('path', wrong_handler),
        )
        with self.assertRaises(TypeError) as context:
            App(routes=routes)
        self.assertIn('subclass of Handler', str(context.exception))

    @mock.patch.object(Response, 'handle')
    def test_route(self, mocked):
        def side_effect(*args, **kwargs):
            self.assertTupleEqual(('arg', ), args)
            self.assertDictEqual(
                dict(kwarg='kwarg', path='conflict_name'),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        app.route('/', 'arg', kwarg='kwarg', path='conflict_name')(Response)
        app.get_handler('/')
        self.assertEqual(1, mocked.call_count)

    @mock.patch.object(Response, 'handle')
    def test_route__routes(self, mocked):
        def side_effect(*args, **kwargs):
            self.assertTupleEqual(('arg1', 'arg2'), args)
            self.assertDictEqual(
                dict(kwarg1='kwarg1', kwarg2='kwarg2', kwarg=2),
                kwargs,
            )

        mocked.side_effect = side_effect
        app = App()
        routes = (
            Route('path', Response, 'arg2', kwarg2='kwarg2', kwarg=2),
        )
        app.route('/', 'arg1', kwarg1='kwarg1', kwarg=1)(routes)
        app.get_handler('/path')
        self.assertEqual(1, mocked.call_count)
