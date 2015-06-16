import unittest

from marnadi.route import Routes, Route


class RoutesTestCase(unittest.TestCase):

    def test_empty(self):
        routes = []
        self.assertListEqual([], Routes(routes))

    def test_single_route(self):
        route = Route('/')
        routes = [route]
        self.assertListEqual([route], Routes(routes))

    def test_two_routes(self):
        route = Route('/')
        routes = [route] * 2
        self.assertListEqual([route] * 2, Routes(routes))

    def test_sequence_of_routes(self):
        route = Route('/')
        routes = [[route] * 2]
        self.assertListEqual([route] * 2, Routes(routes))

    def test_two_sequences_of_routes(self):
        route = Route('/')
        routes = [[route] * 2] * 2
        self.assertListEqual([route] * 4, Routes(routes))

    def test_mixed_routes_and_sequences(self):
        route = Route('/')
        routes = [route] * 2 + [[route] * 2] * 2
        self.assertListEqual([route] * 6, Routes(routes))
