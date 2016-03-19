import cv2
from ..opencv import GenericInput

def frame_callback(frame):
    cv2.imshow("preview", frame)


def calibration():
    parser = GenericInput.parser()
    gi = GenericInput()
    gi.run(parser, frame_callback)
