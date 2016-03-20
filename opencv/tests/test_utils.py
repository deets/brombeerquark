import unittest

from bq.opencv import memoize


class TestUtils(unittest.TestCase):

    def test_memoize(self):

        @memoize
        def foobar(*a, **k):
            return object()

        a = foobar(1, 2, 3)
        b = foobar(1, 2, 3)

        self.assertTrue(a is b)
