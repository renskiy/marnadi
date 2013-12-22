import mock
import re
import unittest

from marnadi import wsgi, errors, Route
from marnadi.handlers import Handler


class EnvironTestCase(unittest.TestCase):

    def test_attribute_getter(self):
        original_environ = {
            'wsgi.input': 'input',
            'CONTENT_TYPE': 'content_type',
            'CONTENT_LENGTH': 'content_length',
            'HTTP_COOKIES': 'cookies',
        }
        environ = wsgi.Environ(original_environ)

        self.assertEqual(getattr(environ, 'wsgi.input'), 'input')
        self.assertEqual(environ['wsgi.input'], 'input')

        self.assertEqual(environ.http_content_type, 'content_type')
        self.assertEqual(environ.content_type, 'content_type')
        self.assertEqual(environ['CONTENT_TYPE'], 'content_type')

        self.assertEqual(environ.http_content_length, 'content_length')
        self.assertEqual(environ.content_length, 'content_length')
        self.assertEqual(environ['CONTENT_LENGTH'], 'content_length')

        self.assertEqual(environ.http_cookies, 'cookies')
        self.assertEqual(environ['HTTP_COOKIES'], 'cookies')

        with self.assertRaises(AttributeError):
            getattr(environ, 'unknown_wsgi_key')
        self.assertNotIn('unknown_wsgi_key', environ)


class AppTestCase(unittest.TestCase):

    def _get_handler_args_parametrized_test_case(
        self,
        handler_path,
        nested_handler_path=None,
        expected_args=None,
        expected_kwargs=None,
    ):
        def side_effect(environ, args, kwargs):
            self.assertEqual('environ', environ)
            self.assertListEqual(expected_args or [], list(args))
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        handler = Handler.decorator(lambda *args, **kwargs: None)
        handler.handle = mock.Mock(side_effect=side_effect)
        routes = (
            (handler_path, nested_handler_path is None and handler or (
                (nested_handler_path, handler),
            )),
        )
        app = wsgi.App(routes=routes)
        app.get_handler('/foo/bar')('environ')
        self.assertEqual(1, handler.handle.call_count)

    def test_get_handler_args__no_args(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo/bar',
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
            handler_path=re.compile(r'/(?P<foo>\w+)/bar'),
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler_args__kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)/(?P<bar>\w+)'),
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler_args__arg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/(?P<bar>\w+)'),
            expected_args=['foo'],
            expected_kwargs=dict(bar='bar'),
        )

    def test_get_handler_args__kwarg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)/(\w+)'),
            expected_args=['bar'],
            expected_kwargs=dict(foo='foo'),
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
            nested_handler_path=re.compile(r'/(?P<bar>\w+)'),
            expected_kwargs=dict(bar='bar'),
        )

    def test_get_handler_args__nested_kwarg_const(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)'),
            nested_handler_path='/bar',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler_args__nested_arg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)'),
            nested_handler_path=re.compile(r'/(\w+)'),
            expected_args=['foo', 'bar'],
        )

    def test_get_handler_args__nested_kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)'),
            nested_handler_path=re.compile(r'/(?P<bar>\w+)'),
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler_args__nested_arg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)'),
            nested_handler_path=re.compile(r'/(?P<bar>\w+)'),
            expected_args=['foo'],
            expected_kwargs=dict(bar='bar'),
        )

    def test_get_handler_args__nested_kwarg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)'),
            nested_handler_path=re.compile(r'/(\w+)'),
            expected_args=['bar'],
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__handler_not_found(self):
        app = wsgi.App()
        with self.assertRaises(errors.HttpError) as context:
            app.get_handler('unknown_path')
        error = context.exception
        self.assertEqual('404 Not Found', error.status)

    @Handler.decorator
    def expected_handler(self, *args, **kwargs):
        pass

    @Handler.decorator
    def unexpected_handler(self, *args, **kwargs):
        pass

    def _get_handler_parametrized_test_case(
        self,
        routes,
        requested_path,
        expected_args=None,
        expected_kwargs=None,
    ):
        def side_effect(environ, args, kwargs):
            self.assertEqual('environ', environ)
            self.assertListEqual(expected_args or [], list(args))
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        self.expected_handler.handle = mock.Mock(side_effect=side_effect)
        self.unexpected_handler.handle = mock.Mock()
        app = wsgi.App(routes=routes)
        app.get_handler(requested_path)('environ')
        self.assertEqual(1, self.expected_handler.handle.call_count)
        self.assertEqual(0, self.unexpected_handler.handle.call_count)

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
                Route('/', self.expected_handler, 'foo', 'bar', baz='baz'),
            ),
            requested_path='/',
            expected_args=['foo', 'bar'],
            expected_kwargs={'baz': 'baz'},
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
                      self.expected_handler, 'foo', 'bar', baz='baz'),
            ),
            requested_path='/baz',
            expected_args=['foo', 'bar', 'baz'],
            expected_kwargs={'baz': 'baz'},
        )

    def test_get_handler_predefined__regexp_route_kwargs_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(?P<baz>bar)'),
                      self.expected_handler, baz='baz'),
            ),
            requested_path='/bar',
            expected_kwargs={'baz': 'baz'},
        )

    def test_get_handler_predefined__regexp_route_complex(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route(re.compile(r'/(?P<foo>foo)/(bar)'),
                      self.expected_handler, 'foo', baz='baz'),
            ),
            requested_path='/foo/bar',
            expected_args=['foo', 'bar'],
            expected_kwargs={'baz': 'baz', 'foo': 'foo'},
        )