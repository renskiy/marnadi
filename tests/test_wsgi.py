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
