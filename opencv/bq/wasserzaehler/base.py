import math

import cv2
import numpy as np


from ..opencv import (
    memoize,
    cv2_3,
    RED,
    YELLOW,
)


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


def find_arrow_direction(contours, preview_image=None, scale=1.0):
    contours = [
        # return ((cx, cy), radius)
        (cv2.minEnclosingCircle(contour), contour)
        for contour in contours
    ]
    # only take the biggest one, based on circle radius
    contours.sort(key=lambda c: c[0][1])
    ((ecx, ecy), radius), contour = contours[-1]

    if preview_image is not None:
        cv2.circle(
            preview_image,
            (int(ecx), int(ecy)),
            int(radius),
            RED,
        )

    M = cv2.moments(contour)

    if M['m00']:
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])

        if preview_image is not None:
            cv2.circle(
                preview_image,
                (cx, cy),
                int(5 / scale),
                YELLOW,
            )

            cv2.line(
                preview_image,
                (cx, cy),
                (int(ecx), int(ecy)),
                (0, 255, 0), 2,
            )
            return math.atan2(ecy - cy, ecx - cx)
