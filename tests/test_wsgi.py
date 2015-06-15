import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from marnadi.response import Response
from marnadi.errors import HttpError
from marnadi.route import Route
from marnadi.utils import Lazy
from marnadi.wsgi import App

_test_handler = Response

_test_route_1 = Route('a', _test_handler)
_test_route_2 = Route('b', _test_handler)

_test_routes = (
    _test_route_1,
    _test_route_2,
)


class AppTestCase(unittest.TestCase):

    def test_get_handler__explicit_lazy_route_match(self):
        lazy_route = Lazy('%s._test_route_1' % __name__)
        app = App([lazy_route])
        app.get_handler('a')

    def test_get_handler__implicit_lazy_route_match(self):
        lazy_route = '%s._test_route_1' % __name__
        app = App([lazy_route])
        app.get_handler('a')

    def test_get_handler__explicit_lazy_subroute_match(self):
        route = Route('/', subroutes=(
            Lazy('%s._test_route_1' % __name__),
        ))
        app = App([route])
        app.get_handler('/a')

    def test_get_handler__implicit_lazy_subroute_match(self):
        route = Route('/', subroutes=(
            '%s._test_route_1' % __name__,
        ))
        app = App([route])
        app.get_handler('/a')

    class expected_handler(Response):
        pass

    class unexpected_handler(Response):
        pass

    def _get_handler_parametrized_test_case(
        self,
        routes,
        requested_path,
        expected_kwargs=None,
    ):
        app = App(routes=routes)
        partial = app.get_handler(requested_path)
        actual_handler = partial.func.__self__
        self.assertIs(actual_handler, self.expected_handler)
        self.assertIsNot(actual_handler, self.unexpected_handler)
        self.assertDictEqual(expected_kwargs or {}, partial.keywords)

    def test_get_handler__empty_route_handler_error(self):
        with self.assertRaises(HttpError) as context:
            self._get_handler_parametrized_test_case(
                routes=(
                    Route('/'),
                ),
                requested_path='/',
            )
        self.assertEqual('404 Not Found', context.exception.status)

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
                Route('/foo', subroutes=(
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', subroutes=(
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__nested_expected_params_url2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', subroutes=(
                    Route('/{bar}', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo', bar='bar'),
        )

    def test_get_handler__nested_expected_params_url2_collision(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/{foo}', subroutes=(
                    Route('/{foo}', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='bar'),
        )

    def test_get_handler__nested_expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/bar', self.expected_handler),
                ), params=dict(foo='foo')),
            ),
            requested_path='/foo/bar',
            expected_kwargs=dict(foo='foo'),
        )

    def test_get_handler__nested_expected_params_route2(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
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
                Route('/foo', subroutes=(
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
                Route('/{foo}', subroutes=(
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
                Route('/{foo}', subroutes=(
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
                Route('/foo', subroutes=(
                    Route('', self.unexpected_handler),
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/bar', self.expected_handler),
                    Route('', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_unexpected_expected_half(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.unexpected_handler, subroutes=(
                    Route('/bar', self.expected_handler),
                )),
            ),
            requested_path='/foo/bar',
        )

    def test_get_handler__nested_expected_unexpected_half(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', self.expected_handler, subroutes=(
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo',
        )

    def test_get_handler__nested2_expected_unexpected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/baz', self.expected_handler),
                )),
                Route('/foo', subroutes=(
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested2_unexpected_expected(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/bar', self.unexpected_handler),
                )),
                Route('/foo', subroutes=(
                    Route('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/baz',
        )

    def test_get_handler__nested2_unexpected_expected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar', self.unexpected_handler),
                )),
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz', self.expected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested2_expected_unexpected_params_url(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz', self.expected_handler),
                )),
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar', self.unexpected_handler),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg'),
        )

    def test_get_handler__nested2_unexpected_expected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
                Route('/foo', subroutes=(
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
            ),
            requested_path='/foo/baz',
            expected_kwargs=dict(f2=2),
        )

    def test_get_handler__nested2_expected_unexpected_params_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo', subroutes=(
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
                Route('/foo', subroutes=(
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
            ),
            requested_path='/foo/baz',
            expected_kwargs=dict(f2=2),
        )

    def test_get_handler__nested2_unexpected_expected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2),
        )

    def test_get_handler__nested2_expected_unexpected_params_url_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz', self.expected_handler, params=dict(f2=2)),
                )),
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar', self.unexpected_handler, params=dict(f1=1)),
                )),
            ),
            requested_path='/foo/kwarg/baz',
            expected_kwargs=dict(kwarg2='kwarg', f2=2),
        )

    def test_get_handler__nested2_unexpected_expected_params_url2_route(self):
        self._get_handler_parametrized_test_case(
            routes=(
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                )),
                Route('/foo/{kwarg2}', subroutes=(
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
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                )),
                Route('/foo/{kwarg1}', subroutes=(
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
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
                Route('/foo/{kwarg2}', subroutes=(
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
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
                Route('/foo/{kwarg1}', subroutes=(
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
                Route('/foo/{kwarg1}', subroutes=(
                    Route('/bar/{bar}', self.unexpected_handler,
                          params=dict(f1=1)),
                ), params=dict(z1='z1')),
                Route('/foo/{kwarg2}', subroutes=(
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
                Route('/foo/{kwarg2}', subroutes=(
                    Route('/baz/{baz}', self.expected_handler,
                          params=dict(f2=2)),
                ), params=dict(z2='z2')),
                Route('/foo/{kwarg1}', subroutes=(
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
                    Route('/foo', subroutes=(
                        Route('/baz', self.expected_handler),
                    )),
                    Route('/foo', subroutes=(
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
                    Route('/foo', subroutes=(
                        Route('/bar', self.unexpected_handler),
                    )),
                    Route('/foo', subroutes=(
                        Route('/baz', self.expected_handler),
                    )),
                ),
                requested_path='/foo',
            )
        self.assertEqual('404 Not Found', context.exception.status)

    def test_route(self):
        app = App()
        app.route('/{foo}', params=dict(kwarg='kwarg'))(Response)
        partial = app.get_handler('/foo')
        self.assertDictEqual(dict(kwarg='kwarg', foo='foo'), partial.keywords)
