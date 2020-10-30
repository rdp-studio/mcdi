from math import radians, sin, cos


def vector_build(a, r):
    i = radians(abs(a) + 90)
    rx, ry = cos(i), sin(i)
    dx, dy = rx * r, ry * r

    if a < 0:
        return dx, dy
    return -dx, dy


class Frontend(object):
    __author__ = "undefined"

    def __init__(self):
        pass

    def get_play_cmd(self, **kwargs) -> str:
        pass

    def get_stop_cmd(self, **kwargs) -> str:
        pass
