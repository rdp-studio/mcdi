from enum import Enum, unique
from math import floor, ceil


class Soma(object):
    soma_long_safe = (
        1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        38, 39, 40, 41, 42, 43, 44, 45, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 120)

    @classmethod
    def play_cmd(cls, prog, note, v, pan, pitch, long, **kwargs):
        abs_pan = (pan - 64) / 32
        left_shift = - abs_pan
        front_shift = 2 - abs(abs_pan)
        relative_v = v / 255

        if prog in cls.soma_long_safe and long:
            prog = str(prog) + "c"
        return f"execute as @a at @s run playsound {prog}.{note} voice @s " \
               f"^{left_shift} ^ ^{front_shift} {relative_v} {pitch}"

    @classmethod
    def stop_cmd(cls, prog, note, long, **kwargs):
        if prog in cls.soma_long_safe and long:
            prog = str(prog) + "c"
        return f"execute as @a at @s run stopsound @s voice {prog}.{note}"
