import cv2
import numpy as np
import json

from ..opencv import (
    GenericInput,
    Bunch,
    GREEN,
    PINK,
    WHITE,
    RED,
    create_hsv_preview,
    colorbar,
    Atan2Monotizer,
    RevolutionCounter,
)

from .base import (
    create_color_corrected_roi,
    filter_for_color_range,
    find_contours,
    find_arrow_direction,
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

WINDOWNAME = "preview"


class Calibration(GenericInput):

    def __init__(self, *a, **k):
        super(Calibration, self).__init__(*a, **k)
        self._revolution_filter = Atan2Monotizer() | RevolutionCounter()

        cv2.namedWindow(WINDOWNAME)
        self._settings = Bunch(**DEFAULT_SETTINGS)
        if self.opts.settings is not None:
            with open(self.opts.settings) as inf:
                self._settings = Bunch(**json.load(inf))


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


    def _update_settings(self, *_a):
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


    @property
    def settings(self):
        return self._settings


    def frame_callback(self, frame):
        self._update_settings()
        s = self.settings

        opts = self.opts
        self.process(frame)

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


    def setup(self, frame, minsize=20):

        cv2.createTrackbar("cmix", WINDOWNAME, 0, 1000, self._update_settings)
        cv2.createTrackbar("cH", WINDOWNAME, 0, 179, self._update_settings)
        cv2.createTrackbar("Hhigh", WINDOWNAME, 0, 179, self._update_settings)
        cv2.createTrackbar("Hlow", WINDOWNAME, 0, 179, self._update_settings)
        cv2.createTrackbar("Shigh", WINDOWNAME, 0, 255, self._update_settings)
        cv2.createTrackbar("Slow", WINDOWNAME, 0, 255, self._update_settings)
        cv2.createTrackbar("Vhigh", WINDOWNAME, 0, 255, self._update_settings)
        cv2.createTrackbar("Vlow", WINDOWNAME, 0, 255, self._update_settings)
        cv2.createTrackbar("blur", WINDOWNAME, 3, 5, self._update_settings)
        cv2.createTrackbar("left", WINDOWNAME, 0, frame.shape[1], self._update_settings)
        cv2.createTrackbar("top", WINDOWNAME, 0, frame.shape[0], self._update_settings)
        cv2.createTrackbar("width", WINDOWNAME, minsize, frame.shape[1] - minsize, self._update_settings)
        cv2.createTrackbar("height", WINDOWNAME, minsize, frame.shape[0] - minsize, self._update_settings)
        self._propagate_settings()


    def augment_parser(self, parser):
        parser.add_argument(
            "--scale",
            help="Scale down input - but just for displaying!",
            type=float,
        )
        parser.add_argument(
            "--settings",
        )


    def process(self, frame):
        s = self.settings
        opts = self.opts
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
            text = "revs: %i" % self._revolution_filter.feed(direction)
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

def calibration():
    gi = Calibration()

    gi.run()
    print json.dumps(gi.settings.dict())
