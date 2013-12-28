import unittest

from marnadi import Lazy

_test_tuple = ('foo', 'bar')

_test_list = ['foo', 'bar']

_test_set = set(('foo', 'bar'))

_test_dict = {'foo': 'bar'}

_test_str = 'foo'


def _test_function(*args, **kwargs):
    return args, kwargs


class _TestClass:
    pass


class LazyTestCase(unittest.TestCase):

    def test_lazy_tuple(self):
        lazy_tuple = Lazy('%s._test_tuple' % __name__)
        self.assertTupleEqual(tuple(lazy_tuple), ('foo', 'bar'))

    def test_lazy_list(self):
        lazy_list = Lazy('%s._test_list' % __name__)
        self.assertListEqual(list(lazy_list), ['foo', 'bar'])

    def test_lazy_set(self):
        lazy_set = Lazy('%s._test_set' % __name__)
        self.assertSetEqual(set(lazy_set), set(('foo', 'bar')))

    def test_lazy_dict(self):
        lazy_dict = Lazy('%s._test_dict' % __name__)
        self.assertDictEqual(dict(lazy_dict), {'foo': 'bar'})

    def test_lazy_str(self):
        lazy_str = Lazy('%s._test_str' % __name__)
        self.assertEqual('foo', str(lazy_str))

    def test_lazy_class(self):
        lazy_class = Lazy('%s._TestClass' % __name__)
        self.assertIsInstance(lazy_class(), _TestClass)

    def test_lazy_function__no_args(self):
        lazy_function = Lazy('%s._test_function' % __name__)
        self.assertEqual(lazy_function(), ((), {}))

    def test_lazy_function__args(self):
        lazy_function = Lazy('%s._test_function' % __name__)
        self.assertEqual(
            lazy_function('foo', 'bar'),
            (('foo', 'bar'), {}),
        )

    def test_lazy_function__kwargs(self):
        lazy_function = Lazy('%s._test_function' % __name__)
        self.assertEqual(
            lazy_function(foo='bar'),
            ((), {'foo': 'bar'}),
        )

    def test_lazy_function__args_kwargs(self):
        lazy_function = Lazy('%s._test_function' % __name__)
        self.assertEqual(
            lazy_function('foo', 'bar', foo='bar'),
            (('foo', 'bar'), {'foo': 'bar'}),
        )
