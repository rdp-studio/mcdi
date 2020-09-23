from math import radians, sin, cos


def get_phase_point(t, r):
    i = radians(abs(t) + 90)
    rx, ry = cos(i), sin(i)
    dx, dy = rx * r, ry * r

    if t < 0:
        return dx, dy
    return -dx, dy


class Frontend(object):
    def __init__(self):
        pass

    def get_play_cmd(self, **kwargs) -> str:
        pass

    def get_stop_cmd(self, **kwargs) -> str:
        pass
