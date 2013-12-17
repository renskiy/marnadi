import re
import unittest

from marnadi import wsgi, errors


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
        def handler(environ, args, kwargs):
            self.assertEqual('environ', environ)
            self.assertListEqual(expected_args or [], args)
            self.assertDictEqual(expected_kwargs or {}, kwargs)

        routes = (
            (handler_path, nested_handler_path is None and handler or (
                (nested_handler_path, handler),
            )),
        )
        app = wsgi.App(routes=routes)
        app.get_handler('/foo/bar')('environ')

    def test_get_handler_args__no_args(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo/bar',
        )

    def test_get_handler_args__arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/bar$'),
            expected_args=['foo'],
        )

    def test_get_handler_args__arg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/(\w+)$'),
            expected_args=['foo', 'bar'],
        )

    def test_get_handler_args__kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)/bar$'),
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler_args__kwarg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)/(?P<bar>\w+)$'),
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler_args__arg_kwarg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(\w+)/(?P<bar>\w+)$'),
            expected_args=['foo'],
            expected_kwargs=dict(bar='bar'),
        )

    def test_get_handler_args__kwarg_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path=re.compile(r'/(?P<foo>\w+)/(\w+)$'),
            expected_args=['bar'],
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler_args__nested_const_arg(self):
        self._get_handler_args_parametrized_test_case(
            handler_path='/foo',
            nested_handler_path=re.compile(r'/(\w+)$'),
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
            nested_handler_path=re.compile(r'/(?P<bar>\w+)$'),
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
            nested_handler_path=re.compile(r'/(\w+)$'),
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
