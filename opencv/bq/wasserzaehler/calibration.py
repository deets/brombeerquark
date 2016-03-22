import cv2
import numpy as np
import json

from ..opencv import (
    GenericInput,
    Bunch,
    GREEN,
    PINK,
    create_hsv_preview,
    colorbar,
)

from .base import (
    create_color_corrected_roi,
    filter_for_color_range,
    find_contours,
    find_arrow_direction,
)


SETTINGS = None

def get_settings(windowname="preview"):
    if SETTINGS is not None:
        return SETTINGS

    d = {}
    for key in [
            "Hhigh", "Hlow", "Shigh",
            "Slow", "Vhigh", "Vlow",
            "left", "top", "width",
            "height", "cH", "blur",
            ]:
        d[key] = cv2.getTrackbarPos(key, windowname)

    for key in ["cmix"]:
        d[key] = cv2.getTrackbarPos(key, windowname) / 1000.0

    return Bunch(**d)


def process(opts, frame, s):
    roi = create_color_corrected_roi(frame, s)

    # create a preview with the percieved colors
    # to gauge the color-space filtering
    cv2.imshow(
        "hsvpreview",
        create_hsv_preview(roi),
    )

    roi = filter_for_color_range(roi, s)
    contours = find_contours(roi, s)

    # convert back for preview
    roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

    if len(contours) > 0:
        cv2.drawContours(roi, contours, -1, PINK, 3)
        direction = find_arrow_direction(contours, roi, opts.scale)

    cv2.imshow("roi", roi)

    cbar = colorbar()
    cbar[0,s.Hlow,:] = [255, 255, 255]
    cbar[0,s.Hhigh,:] = [255, 255, 255]
    cbar[0,s.cH,:] = [0, 0, 0]

    colorbar_stretched = np.zeros((10, 180, 3), dtype="uint8")

    for i in xrange(10):
        colorbar_stretched[i,::] = cbar
    cv2.imshow("colorbar",
        colorbar_stretched,
    )


class Calibration(GenericInput):


    def frame_callback(self, frame):
        opts = self.opts
        s = get_settings()

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


    def setup(self, frame, windowname="preview", minsize=20):
        cv2.namedWindow(windowname)
        def nop(*_a):
            pass

        cv2.createTrackbar("cmix", windowname, 0, 1000, nop)
        cv2.createTrackbar("cH", windowname, 0, 179, nop)
        cv2.createTrackbar("Hhigh", windowname, 0, 179, nop)
        cv2.createTrackbar("Hlow", windowname, 0, 179, nop)
        cv2.createTrackbar("Shigh", windowname, 0, 255, nop)
        cv2.createTrackbar("Slow", windowname, 0, 255, nop)
        cv2.createTrackbar("Vhigh", windowname, 0, 255, nop)
        cv2.createTrackbar("Vlow", windowname, 0, 255, nop)
        cv2.createTrackbar("blur", windowname, 3, 5, nop)
        cv2.createTrackbar("left", windowname, 0, frame.shape[1], nop)
        cv2.createTrackbar("top", windowname, 0, frame.shape[0], nop)
        cv2.createTrackbar("width", windowname, minsize, frame.shape[1] - minsize, nop)
        cv2.createTrackbar("height", windowname, minsize, frame.shape[0] - minsize, nop)


    def augment_parser(self, parser):
        parser.add_argument(
            "--scale",
            help="Scale down input - but just for displaying!",
            type=float,
        )
        parser.add_argument(
            "--settings",
        )


def calibration():
    global SETTINGS

    gi = Calibration()

    if gi.opts.settings is not None:
        with open(gi.opts.settings) as inf:
            s = json.load(inf)
            SETTINGS = Bunch(**s)

    gi.run()
    print json.dumps(get_settings().dict())
