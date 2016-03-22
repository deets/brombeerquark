import json

import numpy as np
import cv2


from ..opencv import (
    Bunch,
    GREEN,
    PINK,
    RED,
    YELLOW,
    WHITE,
    colorbar,
    create_hsv_preview,
)

from .base import (
    Wasserzaehler,
)


WINDOWNAME = "preview"


class Calibration(Wasserzaehler):

    def __init__(self, *a, **k):
        super(Calibration, self).__init__(*a, **k)
        cv2.namedWindow(WINDOWNAME)


    def _propagate_settings(self):
        for key in [
                "Hhigh", "Hlow", "Shigh",
                "Slow", "Vhigh", "Vlow",
                "left", "top", "width",
                "height", "cH", "blur",
                ]:
            value = getattr(self.settings, key)
            cv2.setTrackbarPos(key, WINDOWNAME, value)

        for key in ["cmix"]:
            value = getattr(self.settings, key)
            cv2.setTrackbarPos(key, WINDOWNAME, int(value * 1000))


    def _update_settings(self):
        d = {}
        for key in [
                "Hhigh", "Hlow", "Shigh",
                "Slow", "Vhigh", "Vlow",
                "left", "top", "width",
                "height", "cH", "blur",
                ]:
            d[key] = cv2.getTrackbarPos(key, WINDOWNAME)

        for key in ["cmix"]:
            d[key] = cv2.getTrackbarPos(key, WINDOWNAME) / 1000.0

        self._settings = Bunch(**d)


    def color_range_filtered_roi(self, roi):
        self._color_range_filtered_roi = roi


    def found_contours(self, contours):
        self._found_contours = contours


    def enclosing_circle_and_centroid(self, circle, centroid):
        self._circle = circle
        self._centroid = centroid


    def frame_callback(self, frame):
        self._update_settings()
        s = self.settings

        opts = self.opts
        super(Calibration, self).frame_callback(frame)

        # convert back for preview
        roi = cv2.cvtColor(self._color_range_filtered_roi, cv2.COLOR_GRAY2BGR)

        if self._found_contours:
            cv2.drawContours(roi, self._found_contours, -1, PINK, 3)

        text = "revs: %i" % self.revolutions
        cv2.putText(
            roi,
            text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.0,
            RED,
            3,
        )
        cv2.putText(
            roi,
            text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.0,
            WHITE,
        )

        scale = self.opts.scale
        (ecx, ecy), radius = self._circle
        cx, cy = self._centroid

        cv2.circle(
            roi,
            (int(ecx), int(ecy)),
            int(radius),
            RED,
        )
        cv2.circle(
            roi,
            (cx, cy),
            int(5 / scale),
            YELLOW,
        )

        cv2.line(
            roi,
            (cx, cy),
            (int(ecx), int(ecy)),
            (0, 255, 0), 2,
        )

        cv2.imshow("roi", roi)


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


    def setup(self, frame):
        super(Calibration, self).setup(frame)

        def nop(*_a):
            pass

        minsize = 20

        cv2.createTrackbar("cmix", WINDOWNAME, 0, 1000, nop)
        cv2.createTrackbar("cH", WINDOWNAME, 0, 179, nop)
        cv2.createTrackbar("Hhigh", WINDOWNAME, 0, 179, nop)
        cv2.createTrackbar("Hlow", WINDOWNAME, 0, 179, nop)
        cv2.createTrackbar("Shigh", WINDOWNAME, 0, 255, nop)
        cv2.createTrackbar("Slow", WINDOWNAME, 0, 255, nop)
        cv2.createTrackbar("Vhigh", WINDOWNAME, 0, 255, nop)
        cv2.createTrackbar("Vlow", WINDOWNAME, 0, 255, nop)
        cv2.createTrackbar("blur", WINDOWNAME, 3, 5, nop)
        cv2.createTrackbar("left", WINDOWNAME, 0, frame.shape[1], nop)
        cv2.createTrackbar("top", WINDOWNAME, 0, frame.shape[0], nop)
        cv2.createTrackbar("width", WINDOWNAME, minsize, frame.shape[1] - minsize, nop)
        cv2.createTrackbar("height", WINDOWNAME, minsize, frame.shape[0] - minsize, nop)
        self._propagate_settings()


    def augment_parser(self, parser):
        super(Calibration, self).augment_parser(parser)
        parser.add_argument(
            "--scale",
            help="Scale down input - but just for displaying!",
            type=float,
        )


    def color_adjusted_roi(self, roi):
        # create a preview with the percieved colors
        # to gauge the color-space filtering
        cv2.imshow(
            "hsvpreview",
            create_hsv_preview(roi),
        )



def calibration():
    gi = Calibration()

    gi.run()
    print json.dumps(gi.settings.dict())
