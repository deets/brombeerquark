import cv2

IS_TWO = cv2.__version__.startswith("2.")


class cv2_3(object):

    @staticmethod
    def findContours(*a, **k):
        res = cv2.findContours(*a, **k)
        if IS_TWO:
            res = (None,) + res
        return res
