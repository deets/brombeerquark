import cv2
import numpy as np
import json

from ..opencv import (
    GenericInput,
    Bunch,
    GREEN,
    YELLOW,
    RED,
    create_hsv_preview,
    memoize,
    colorbar,
    cv2_3,
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


@memoize
def complementary_image(H, shape):
    res = np.zeros(shape, dtype="uint8")
    res[:,:,0] = H
    res[:,:, 1:] = [255, 255]
    return cv2.cvtColor(res, cv2.COLOR_HSV2BGR)


def process(opts, frame, s):
    roi = frame[s.top:s.top + s.height, s.left:s.left + s.width]

    if s.cmix > 0:
        comp_img = complementary_image(s.cH, roi.shape)
        roi = cv2.addWeighted(roi, 1.0 - s.cmix, comp_img, s.cmix, 0)

    roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # create a preview with the percieved colors
    # to gauge the color-space filtering
    cv2.imshow(
        "hsvpreview",
        create_hsv_preview(roi),
    )

    lower = np.array([s.Hlow, s.Slow, s.Vlow], dtype="uint8")
    upper = np.array([s.Hhigh, s.Shigh, s.Vhigh], dtype="uint8")
    roi = cv2.inRange(roi, lower, upper)

    _, contours, _ = cv2_3.findContours(
        roi.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    roi = cv2.GaussianBlur(roi, (s.blur, s.blur), 0)
    roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

    if len(contours) > 0:
        cv2.drawContours(roi, contours, -1, (0, 255, 255), 3)
        contours = [
            # return ((cx, cy), radius)
            (cv2.minEnclosingCircle(contour), contour)
            for contour in contours
        ]
        # only take the biggest one, based on circle radius
        contours.sort(key=lambda c: c[0][1])
        ((ecx, ecy), radius), contour = contours[-1]
        cv2.circle(
            roi,
            (int(ecx), int(ecy)),
            int(radius),
            RED,
        )
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


            cv2.line(
                roi,
                (cx, cy),
                (int(ecx), int(ecy)),
                (0, 255, 0), 2,
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


def frame_callback(opts, frame):
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


def setup(opts, frame, windowname="preview", minsize=20):

    cv2.namedWindow(windowname)
    def nop(*a):
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


def calibration():
    global SETTINGS

    parser = GenericInput.parser()
    parser.add_argument(
        "--scale",
        help="Scale down input - but just for displaying!",
        type=float,
    )
    parser.add_argument(
        "--settings",
    )

    gi = GenericInput(parser)

    if gi.opts.settings is not None:
        with open(gi.opts.settings) as inf:
            s = json.load(inf)
            SETTINGS = Bunch(**s)

    gi.run(
        frame_callback,
        setup=setup,
        )

    print json.dumps(get_settings().dict())
