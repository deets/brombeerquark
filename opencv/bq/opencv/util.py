from functools import wraps
import operator
import math

import cv2
import numpy as np


GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (0, 255, 255)

class Bunch(object):

    def __init__(self, **k):
        self.__dict__.update(k)


    def dict(self):
        return self.__dict__


def create_hsv_preview(img):
    """
    Takes an HSV-image, and returns
    a copy where the SV components
    are maxed out, in BGR-colorspace.

    This allows to perceive the way sectioning
    in H-space  works.
    """
    hsv_preview = img.copy()
    hsv_preview[:,:,1:] = [255, 255]
    return cv2.cvtColor(hsv_preview, cv2.COLOR_HSV2BGR)


def memoize(f):
    @wraps(f)
    def _d(*a, **k):
        key = a, tuple((key, value) for key, value in k.iteritems())
        if key not in f._cache:
           f._cache[key] = f(*a, **k)
        return f._cache[key]

    f._cache = {}
    return _d


def colorbar():
    return cv2.cvtColor(
        np.array(
            [[(i, 255, 255) for i in xrange(180)]],
            dtype="uint8",
        ),
        cv2.COLOR_HSV2BGR,
    )



class RevolutionCounter(object):
    """
    A simple class to count revolutions
    based on input of a continuous, mononotic(!)
    sequence of atan2-values with each distinct
    step not farther than math.pi/2

    The counter is quadrant-based: the first value determines
    the initial quadrant, and whenever the input enters this quadrant
    again, it will trigger an increase in revolutions.
    """

    def __init__(self):
        self.revolutions = 0
        self._initial_quadrant = None
        self._in_quadrant = True


    def feed(self, input_):
        q = self._quadrant(input_)
        if self._initial_quadrant is None:
            self._initial_quadrant = q
            self._in_quadrant = True
        # we count when re-entering the quadrant
        if not self._in_quadrant and q == self._initial_quadrant:
            self._initial_quadrant = True
            self._in_quadrant = True
            self.revolutions += 1
        elif self._in_quadrant and q != self._initial_quadrant:
            self._in_quadrant = False
        return self.revolutions


    def _quadrant(self, input_):
        """
        1 | 0
        -----
        2 | 3
        """
        if input_ >= 0:
            return 0 if input_ < math.pi / 2 else 1
        else:
            return 2 if input_ < -math.pi / 2 else 3


class Atan2Monotizer(object):

    def __init__(self, clockwise=True):
        self._last_input = None
        self._v = None
        self._op = operator.le if clockwise else operator.ge


    def feed(self, input_):
        if self._last_input is not None:
            diff = input_ - self._last_input
            while diff > math.pi / 2.0:
                diff -= math.pi
            while diff < -math.pi / 2.0:
                diff += math.pi

            if self._op(diff, 0):
                self._last_input = input_
        else:
            self._last_input = input_

        return self._last_input
