import cv2
import time
import argparse


class GenericInput(object):


    @classmethod
    def parser(cls, *a, **k):
        parser = argparse.ArgumentParser(*a, **k)
        parser.add_argument("--movie")
        parser.add_argument("--image")
        parser.add_argument("--image-fps", type=int, default=30)
        return parser


    def run(self, parser, frame_callback):
        opts = parser.parse_args()
        if opts.movie is not None:
            capture = cv2.VideoCapture(opts.movie)
        elif opts.image is not None:
            capture = self.single_image_capture(
                opts.image,
                opts.image_fps,
            )
        else:
            raise Exception("no input data specified")
        while True:
            grabbed, frame = capture.read()
            if not grabbed:
                break
            frame_callback(frame)

            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break


    def single_image_capture(self, imagename, fps):
        img = cv2.imread(imagename)
        class Capture(object):
            def __init__(self):
                self._timestamp = time.time() - 1.0
                self._period = 1.0 / fps

            def read(self):
                elapsed = time.time() - self._timestamp
                if elapsed <= self._period:
                    time.sleep(self._period - elapsed)

                self._timestamp = time.time()
                return True, img
        return Capture()
