import cv2
import numpy as np
import json
from functools import partial

from ..opencv import (
    GenericInput,
    Bunch,
    GREEN,
    YELLOW,
    RED,
)

SETTINGS = None

def get_settings(opts, windowname="preview"):
    global SETTINGS
    if opts.settings is None:

        d = {}
        for key in [
                "Hhigh", "Hlow", "Shigh",
                "Slow", "Vhigh", "Vlow",
                "left", "top", "width",
                "height",
                ]:
            d[key] = cv2.getTrackbarPos(key, windowname)
        return Bunch(**d)
    elif SETTINGS is None:
        with open(opts.settings) as inf:
            s = json.load(inf)
            SETTINGS = Bunch(**s)
    return SETTINGS


def process(opts, frame, s):
    roi = frame[s.top:s.top + s.height, s.left:s.left + s.width]
    green = np.ones(roi.shape, dtype="uint8")
    green[:,:,0] *= 0
    green[:,:,1] *= 255
    green[:,:,2] *= 0
    roi = cv2.addWeighted(roi, 0.9, green, 0.1, 0)
    roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    colorbar = np.array(
            [[(i, 255, 255) for i in xrange(180)]],
            dtype="uint8",
    )
    colorbar[0,s.Hlow,:] = [0, 0, 255]
    colorbar[0,s.Hhigh,:] = [0, 0, 255]

    lower = np.array([s.Hlow, s.Slow, s.Vlow], dtype="uint8")
    upper = np.array([s.Hhigh, s.Shigh, s.Vhigh], dtype="uint8")
    roi = cv2.inRange(roi, lower, upper)

    _, contours, _ = cv2.findContours(
        roi.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    roi = cv2.GaussianBlur(roi, (s.blur, s.blur), 0)
    roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

    if len(contours) > 0:
        cv2.drawContours(roi, contours, -1, (0, 255, 255), 3)
        for contour in contours:
            (cx, cy), radius = cv2.minEnclosingCircle(contour)

            cv2.circle(
                roi,
                (int(cx), int(cy)),
                int(radius),
                RED,
            )
            if radius > s.width * s.contourRadiusRatio:
                M = cv2.moments(contour)

                if M['m00']:
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    cv2.circle(
                        roi,
                        (cx, cy),
                        int(5 / opts.scale),
                        YELLOW,
                    )


    cv2.imshow("roi", roi)
    colorbar_stretched = np.zeros((10, 180, 3), dtype="uint8")
    for i in xrange(10):
        colorbar_stretched[i,::] = colorbar
    cv2.imshow("colorbar",
        cv2.cvtColor(
            colorbar_stretched,
            cv2.COLOR_HSV2BGR,
        )
    )


def frame_callback(opts, frame):
    s = get_settings(opts)

    process(opts, frame, s)

    cv2.rectangle(
        frame,
        (s.left, s.top),
        (s.left + s.width, s.top + s.height),
        GREEN,
        int(1.0 / opts.scale),
    )

    if opts.scale is not None:
        dim = (
            int(frame.shape[1] * opts.scale),
            int(frame.shape[0] * opts.scale)
        )
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    cv2.imshow("preview", frame)


def setup(opts, frame, windowname="preview", minsize=20):

    cv2.namedWindow(windowname)
    def nop(*a):
        pass

    cv2.createTrackbar("Hhigh", windowname, 0, 179, nop)
    cv2.createTrackbar("Hlow", windowname, 0, 179, nop)
    cv2.createTrackbar("Shigh", windowname, 0, 255, nop)
    cv2.createTrackbar("Slow", windowname, 0, 255, nop)
    cv2.createTrackbar("Vhigh", windowname, 0, 255, nop)
    cv2.createTrackbar("Vlow", windowname, 0, 255, nop)
    cv2.createTrackbar("left", windowname, 0, frame.shape[1], nop)
    cv2.createTrackbar("top", windowname, 0, frame.shape[0], nop)
    cv2.createTrackbar("width", windowname, minsize, frame.shape[1] - minsize, nop)
    cv2.createTrackbar("height", windowname, minsize, frame.shape[0] - minsize, nop)


def calibration():
    parser = GenericInput.parser()
    parser.add_argument(
        "--scale",
        help="Scale down input - but just for displaying!",
        type=float,
    )
    parser.add_argument(
        "--settings",
    )
    gi = GenericInput()
    gi.run(
        parser,
        frame_callback,
        setup=setup,
        )

    print json.dumps(get_settings().dict())
