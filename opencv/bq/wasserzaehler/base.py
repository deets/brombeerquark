import math
import json

import cv2
import numpy as np


from ..opencv import (
    memoize,
    Bunch,
    cv2_3,
    GenericInput,
    Atan2Monotizer,
    RevolutionCounter,
)


DEFAULT_SETTINGS = {
    "Hhigh" : 0,
    "Hlow" : 0,
    "Shigh" : 0,
    "Slow" : 0,
    "Vhigh" : 0,
    "Vlow" : 0,
    "left" : 10,
    "top" : 10,
    "width" : 100,
    "height" : 100,
    "cH" : 0,
    "blur" : 3,
    "cmix" : 0,
}


@memoize
def complementary_image(H, shape):
    res = np.zeros(shape, dtype="uint8")
    res[:,:,0] = H
    res[:,:, 1:] = [255, 255]
    return cv2.cvtColor(res, cv2.COLOR_HSV2BGR)


def create_color_corrected_roi(frame, s):
    """
    Cuts out the ROI, and potentially blends
    it with the color correction
    """
    roi = frame[s.top:s.top + s.height, s.left:s.left + s.width]

    if s.cmix > 0:
        comp_img = complementary_image(s.cH, roi.shape)
        roi = cv2.addWeighted(roi, 1.0 - s.cmix, comp_img, s.cmix, 0)

    return cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)


@memoize
def range_array(*a):
    return np.array(a, dtype="uint8")


def filter_for_color_range(roi, s):
    lower = range_array(s.Hlow, s.Slow, s.Vlow)
    upper = range_array(s.Hhigh, s.Shigh, s.Vhigh)
    return cv2.inRange(roi, lower, upper)


def find_contours(roi, s):
    roi = cv2.GaussianBlur(roi, (s.blur, s.blur), 0)

    _, contours, _ = cv2_3.findContours(
        roi.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    return contours


class Wasserzaehler(GenericInput):

    def __init__(self, *a, **k):
        super(Wasserzaehler, self).__init__(*a, **k)
        self._revolution_filter = Atan2Monotizer() | RevolutionCounter()
        self._settings = Bunch(**DEFAULT_SETTINGS)
        if self.opts.settings is not None:
            with open(self.opts.settings) as inf:
                self._settings = Bunch(**json.load(inf))

        self._last_revolution = -1


    @property
    def revolutions(self):
        return self._revolution_filter.revolutions


    @property
    def settings(self):
        return self._settings


    def setup(self, frame):
        super(Wasserzaehler, self).setup(frame)


    def augment_parser(self, parser):
        super(Wasserzaehler, self).augment_parser(parser)
        parser.add_argument(
            "--settings",
        )


    def frame_callback(self, frame):
        s = self.settings
        roi = create_color_corrected_roi(frame, s)

        self.color_adjusted_roi(roi)

        roi = filter_for_color_range(roi, s)
        self.color_range_filtered_roi(roi)
        contours = find_contours(roi, s)
        self.found_contours(contours)

        if len(contours) > 0:
            direction = self.find_arrow_direction(contours)
            self._revolution_filter.feed(direction)

        if self._last_revolution != self.revolutions:
            self._last_revolution = self.revolutions
            print self.revolutions


    def find_arrow_direction(self, contours):
        contours = [
            # return ((cx, cy), radius)
            (cv2.minEnclosingCircle(contour), contour)
            for contour in contours
        ]
        # only take the biggest one, based on circle radius
        contours.sort(key=lambda c: c[0][1])
        ((ecx, ecy), radius), contour = contours[-1]
        M = cv2.moments(contour)

        if M['m00']:
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])

            self.enclosing_circle_and_centroid(
                ((ecx, ecy), radius),
                (cx, cy)
            )
            return math.atan2(ecy - cy, ecx - cx)


    # The following callbacks are for
    # introspection into the processing.
    #
    # They aren't beautiful, but allow
    # the Calibration to show meaningful states
    # to tune the system.

    def color_adjusted_roi(self, roi):
        pass


    def color_range_filtered_roi(self, roi):
        pass


    def found_contours(self, contours):
        pass


    def enclosing_circle_and_centroid(self, circle, centroid):
        pass


def wasserzaehler():
    gi = Wasserzaehler()
    gi.run()
