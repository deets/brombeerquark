from functools import wraps

import cv2
import numpy as np


GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

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
