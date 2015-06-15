import types
import unittest

from marnadi.utils import Lazy

try:
    str = unicode
except NameError:
    pass

_test_tuple = ('foo', 'bar')

_test_list = ['foo', 'bar']

_test_set = set(_test_tuple)

_test_dict = {'foo': 'bar'}

_test_str = 'foo'

_test_bytes = b'foo'

_test_true = True

_test_false = False


def _test_function(*args, **kwargs):
    return args, kwargs


class _TestClass:
    pass

_test_instance = _TestClass()


class LazyTestCase(unittest.TestCase):

    def test_lazy_true(self):
        lazy_true = Lazy('%s._test_true' % __name__)
        self.assertTrue(lazy_true)

    def test_lazy_false(self):
        lazy_true = Lazy('%s._test_false' % __name__)
        self.assertFalse(lazy_true)

    def test_lazy_tuple(self):
        lazy_tuple = Lazy('%s._test_tuple' % __name__)
        self.assertTupleEqual(_test_tuple, tuple(lazy_tuple))

    def test_length_of_lazy_tuple(self):
        lazy_tuple = Lazy('%s._test_tuple' % __name__)
        self.assertEqual(2, len(lazy_tuple))

    def test_lazy_list(self):
        lazy_list = Lazy('%s._test_list' % __name__)
        self.assertListEqual(_test_list, list(lazy_list))

    def test_lazy_set(self):
        lazy_set = Lazy('%s._test_set' % __name__)
        self.assertSetEqual(_test_set, set(lazy_set))

    def test_lazy_dict(self):
        lazy_dict = Lazy('%s._test_dict' % __name__)
        self.assertDictEqual(_test_dict, dict(lazy_dict))

    def test_lazy_str(self):
        lazy_str = Lazy('%s._test_str' % __name__)
        self.assertEqual(_test_str, str(lazy_str))

    def test_lazy_bytes(self):
        lazy_bytes = Lazy('%s._test_bytes' % __name__)
        self.assertEqual(_test_bytes, bytes(lazy_bytes))

    def test_lazy_isinstance(self):
        lazy_instance = Lazy('%s._test_instance' % __name__)
        self.assertIsInstance(lazy_instance, _TestClass)

    def test_lazy_class_instance(self):
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

    def test_lazy__explicit_class(self):
        self.assertIs(_TestClass, Lazy(_TestClass))

    def test_lazy__explicit_function(self):
        self.assertIs(_test_function, Lazy(_test_function))

    def test_lazy__explicit_instance(self):
        self.assertIs(Lazy(_test_instance), _test_instance)

    def test_lazy__explicit_dict(self):
        self.assertIs(_test_dict, Lazy(_test_dict))

    def test_lazy__explicit_list(self):
        self.assertIs(_test_list, Lazy(_test_list))

    def test_lazy__explicit_tuple(self):
        self.assertIs(_test_tuple, Lazy(_test_tuple))

    def test_lazy__explicit_set(self):
        self.assertIs(_test_set, Lazy(_test_set))

    def test_lazy__explicit_none(self):
        self.assertIsNone(Lazy(None))

    def test_lazy__explicit_lazy(self):
        lazy = Lazy('%s._test_instance' % __name__)
        self.assertIs(lazy, Lazy(lazy))

    def test_lazy__explicit_lazy_str(self):
        lazy_str = Lazy('%s._test_str' % __name__)
        self.assertIs(lazy_str, Lazy(lazy_str))

    def test_lazy__module(self):
        lazy = Lazy(__name__)
        self.assertIsInstance(lazy, types.ModuleType)
        self.assertEqual(__name__, lazy.__name__)

    def test_lazy__module_from_package(self):
        lazy = Lazy('marnadi.wsgi')
        self.assertIsInstance(lazy, types.ModuleType)
        self.assertEqual('marnadi.wsgi', lazy.__name__)

    def test_lazy__package(self):
        lazy = Lazy('marnadi')
        self.assertIsInstance(lazy, types.ModuleType)
        self.assertEqual('marnadi', lazy.__name__)

    def test_lazy__package_from_package(self):
        lazy = Lazy('marnadi.http')
        self.assertIsInstance(lazy, types.ModuleType)
        self.assertEqual('marnadi.http', lazy.__name__)
