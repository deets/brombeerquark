import math
import unittest

from bq.opencv import (
    memoize,
    RevolutionCounter,
    Atan2Monotizer,
)


class TestUtils(unittest.TestCase):

    @classmethod
    def produce_rotationdata(cls, revolutions, steps_in_degrees):
        revs = 0
        pos = 0
        while revs < revolutions:
            pos += steps_in_degrees
            revs = abs(pos) // 360
            rad = math.pi * float(pos) / 180.0
            yield revs, math.atan2(math.sin(rad), math.cos(rad))


    def test_memoize(self):

        @memoize
        def foobar(*a, **k):
            return object()

        a = foobar(1, 2, 3)
        b = foobar(1, 2, 3)

        self.assertTrue(a is b)


    def test_revolution_counter_clockwise(self):
        counter = RevolutionCounter()

        for revs, input_ in self.produce_rotationdata(3, -5):
            counter.feed(input_)

        self.assertEqual(3, counter.revolutions)


    def test_revolution_counter_counter_clockwise(self):
        counter = RevolutionCounter()
        for revs, input_ in self.produce_rotationdata(3, 5):
            counter.feed(input_)

        self.assertEqual(3, counter.revolutions)


    def test_atan2_monotizer_clockwise(self):
        original_input = list(i for _, i in self.produce_rotationdata(1, -5))
        for i in xrange(len(original_input) - 1):
            input_ = list(original_input)
            input_[i], input_[i+1] = input_[i+1], input_[i]

            monotizer = Atan2Monotizer()
            output = [monotizer.feed(inp) for inp in input_]
            self.assertEqual(len(input_), len(output))
            # this is a bit underhanded, but due to
            # the complex wrap-around logic it
            # just checks that one value has been produced twice
            self.assertEqual(len(set(input_)) -1, len(set(output)))


    def test_atan2_monotizer_counterclockwise(self):
        original_input = list(i for _, i in self.produce_rotationdata(1, 5))
        for i in xrange(len(original_input) - 1):
            input_ = list(original_input)
            input_[i], input_[i+1] = input_[i+1], input_[i]

            monotizer = Atan2Monotizer(clockwise=False)
            output = [monotizer.feed(inp) for inp in input_]
            self.assertEqual(len(input_), len(output))
            # this is a bit underhanded, but due to
            # the complex wrap-around logic it
            # just checks that one value has been produced twice
            self.assertEqual(len(set(input_)) -1, len(set(output)))
