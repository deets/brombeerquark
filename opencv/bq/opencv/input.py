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


    def __init__(self, parser):
        self.opts = parser.parse_args()


    def run(self, frame_callback, setup=None):
        print "press ESC to quit!"
        opts = self.opts
        capture = self.create_capture(opts)
        setup_called = False

        while True:
            grabbed, frame = capture.read()
            if not grabbed:
                capture = self.create_capture(opts)
                grabbed, frame = capture.read()
                assert grabbed

            if not setup_called:
                setup_called = True
                setup(opts, frame)
            frame_callback(opts, frame)

            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break


    def create_capture(self, opts):
        if opts.movie is not None:
            return cv2.VideoCapture(opts.movie)
        elif opts.image is not None:
            return self.single_image_capture(
                opts.image,
                opts.image_fps,
            )
        else:
            raise Exception("no input data specified")


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
