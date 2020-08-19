# -*- coding: utf-8 -*-
# Copyright: 2020, Diez B. Roggisch, Berlin . All rights reserved.
from collections import deque


class IIRFilter:

    def __init__(self, gain, start=0.0):
        self._gain = gain
        self.value = start

    def feed(self, value):
        self.value += (value - self.value) * self._gain
        return self.value


class FIRFilter:

    def __init__(self, size):
        self._q = deque(maxlen=size)

    def feed(self, value):
        self._q.append(value)
        return self.value

    @property
    def value(self):
        return sum(self._q) / len(self._q)


def main():
    # local here because not needed by IIRFilter
    import time
    import random

    iir = IIRFilter(0.01)
    fir = FIRFilter(10)
    while True:
        v = 100 if random.random() < 0.9 else 0
        print(v, iir.feed(v), fir.feed(v))
        time.sleep(.1)


if __name__ == '__main__':
    main()
