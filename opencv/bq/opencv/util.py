
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)

class Bunch(object):

    def __init__(self, **k):
        self.__dict__.update(k)


    def dict(self):
        return self.__dict__
