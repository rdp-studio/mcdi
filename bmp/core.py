import enum
import math
import sys
from functools import reduce
from operator import add

sys.path.append("..")
from bmp.klass import *


def hsv2rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0:
        r, g, b = v, t, p
    elif hi == 1:
        r, g, b = q, v, p
    elif hi == 2:
        r, g, b = p, v, t
    elif hi == 3:
        r, g, b = p, q, v
    elif hi == 4:
        r, g, b = t, p, v
    elif hi == 5:
        r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return r, g, b


def rgb2hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df / mx
    v = mx
    return h, s, v


class Dirs(enum.Enum):
    XY = 0
    YZ = 1
    XZ = 2


class Mdl(enum.Enum):
    RGB = 0
    HSV = 1


class BlockGenerator(BaseGenerator):
    def __init__(self, blks, dirs=Dirs.XY, abs=None, mdl=Mdl.RGB, *args, **kwargs):
        super(BlockGenerator, self).__init__(*args, **kwargs)

        self.blks = blks
        self.abs = abs
        self.dirs = dirs
        self.mdl = mdl

    def build_pixels(self, resample=Image.LANCZOS):
        self.built_function.clear()

        logging.info(f"Loading pixel(s) from the image file.")

        if self.img.width != self.x and self.img.height != self.y:
            self.img = self.img.resize((self.x, self.y), resample=resample)
        pixels = self.img.load()

        logging.info(f"Building {(pixel_count := self.x * self.y)} pixel(s).")

        for x in range(self.x):
            for y in range(self.y):
                pixel = pixels[x, y]
                min_diff = 255 * 3 + 1
                nearest = None
                for item in reduce(add, self.blks):
                    if self.mdl == Mdl.RGB:
                        diff = self.get_rgb_diff(item, pixel)
                    elif self.mdl == Mdl.HSV:
                        diff = self.get_hsv_diff(item, pixel)
                    else:
                        raise TypeError(f"Invalid color model: {self.mdl}")
                    if diff < min_diff:
                        min_diff = diff
                        nearest = item
                block_name = nearest["block"]
                self.set_block(x, y, block_name)

                if (built_count := x * self.y + y) % 1000 == 0:
                    logging.info(f"Built {built_count} pixel(s), {pixel_count} pixel(s) in all.")

        logging.info("Build procedure finished.")

    def set_block(self, x, y, block):
        if self.dirs == Dirs.XY:
            if not self.abs:
                self.built_function.append(f"setblock ~{x} ~{self.y - y - 1} ~ minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.abs
                self.built_function.append(
                    f"setblock {x + x_shift} {self.y - y - 1 + y_shift} {z_shift} minecraft:{block} replace"
                )
        elif self.dirs == Dirs.YZ:
            if not self.abs:
                self.built_function.append(f"setblock ~ ~{x} ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.abs
                self.built_function.append(
                    f"setblock {z_shift} {x + x_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace"
                )
        elif self.dirs == Dirs.XZ:
            if not self.abs:
                self.built_function.append(f"setblock ~{x} ~ ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.abs
                self.built_function.append(
                    f"setblock {x + x_shift} {z_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace"
                )

    @staticmethod
    def get_rgb_diff(item, pixel):
        color = item["color"]
        r_diff = abs(color[0] - pixel[0])
        g_diff = abs(color[1] - pixel[1])
        b_diff = abs(color[2] - pixel[2])
        return r_diff + g_diff + b_diff

    @staticmethod
    def get_hsv_diff(item, pixel):
        c_h, c_s, c_v = rgb2hsv(*item["color"])
        p_h, p_s, p_v = rgb2hsv(*pixel[:3])
        h_diff = abs(c_h - p_h) / 360 * 255
        s_diff = abs(c_s - p_s) * 255
        v_diff = abs(c_v - p_v) * 255
        return h_diff + s_diff + v_diff


class ParticleGenerator(BaseGenerator):
    def __init__(self, prtcl, dirs=Dirs.XY, abs=None, dthr=True, door=382.5, size=.1, mono=True, *args, **kwargs):
        super(ParticleGenerator, self).__init__(*args, **kwargs)

        self.prtcl = prtcl
        self.abs = abs
        self.dirs = dirs
        self.dthr = dthr
        self.door = door
        self.size = size
        self.mono = mono

    def build_pixels(self, resample=Image.LANCZOS):
        self.built_function.clear()

        logging.info(f"Loading pixel(s) from the image file.")

        if self.img.width != self.x and self.img.height != self.y:
            self.img = self.img.resize((self.x, self.y), resample=resample)
        pixels = self.img.load()

        logging.info(f"Building {(pixel_count := self.x * self.y)} pixel(s).")

        if self.dthr and self.mono:
            logging.info(f"Dithering {pixel_count} pixel(s).")
            self.run_dither(pixels)
            logging.info(f"Dither procedure finished.")

        for x in range(self.x):
            for y in range(self.y):
                pixel = pixels[x, y]
                rx = x * self.size
                ry = y * self.size

                if self.mono and sum(pixel[:3]) > self.door:
                    self.set_mono_particle(rx, ry, pixel)
                elif not self.mono:
                    self.set_color_particle(rx, ry, pixel)

        logging.info(f"Build procedure finished.")

    def get_pos(self, x, y):
        if self.dirs == Dirs.XY:
            if not self.abs:
                return f"~{x} ~{self.y * self.size - y - 1} ~"
            else:
                x_shift, y_shift, z_shift = self.abs
                return f"{x + x_shift} {self.y * self.size - y - 1 + y_shift} {z_shift}"
        elif self.dirs == Dirs.YZ:
            if not self.abs:
                return f"~ ~{x} ~{self.y * self.size - y - 1}"
            else:
                x_shift, y_shift, z_shift = self.abs
                return f"{z_shift} {x + x_shift} {self.y * self.size - y - 1 + y_shift}"
        elif self.dirs == Dirs.XZ:
            if not self.abs:
                return f"~{x} ~ ~{self.y * self.size - y - 1}"
            else:
                x_shift, y_shift, z_shift = self.abs
                return f"{x + x_shift} {z_shift} {self.y * self.size - y - 1 + y_shift}"

    def set_mono_particle(self, x, y, _):
        self.built_function.append(f"particle {self.prtcl} {self.get_pos(x, y)} 0 0 0 0 0 force @a")

    def set_color_particle(self, x, y, pixel):
        r, g, b, a = pixel[0] / 255, pixel[1] / 255, pixel[2] / 255, pixel[3] / 255 if len(pixel) > 3 else 1  # RGBA
        if self.prtcl.endswith("ambient_entity_effect"):
            self.built_function.append(f"particle {self.prtcl} {self.get_pos(x, y)} {r} {g} {b} 1 0 force @a")
        elif self.prtcl.endswith("dust"):
            self.built_function.append(f"particle {self.prtcl} {r} {g} {b} {a} {self.get_pos(x, y)} 0 0 0 0 0 force @a")
        elif self.prtcl.endswith("entity_effect"):
            self.built_function.append(f"particle {self.prtcl} {self.get_pos(x, y)} {r} {g} {b} 1 0 force @a")
        else:
            raise RuntimeError("Invalid particle to use color generation.")

    def run_dither(self, pixels):
        for y in range(1, self.img.height - 1):
            for x in range(1, self.img.width - 1):
                old_pixel = pixels[x, y][:3]
                pixel_val = round(sum(old_pixel) / 765) * 255
                new_pixel = [pixel_val for i in range(0, 3)]
                pixels[x, y] = tuple(new_pixel)
                diff = sum(old_pixel) - sum(new_pixel)

                r, g, b = pixels[x + 1, y][:3]
                pixels[x + 1, y] = round(r + diff * 7 / 16), round(g + diff * 7 / 16), round(b + diff * 7 / 16)
                r, g, b = pixels[x - 1, y + 1][:3]
                pixels[x - 1, y + 1] = round(r + diff * 3 / 16), round(g + diff * 3 / 16), round(b + diff * 3 / 16)
                r, g, b = pixels[x, y + 1][:3]
                pixels[x, y + 1] = round(r + diff * 5 / 16), round(g + diff * 5 / 16), round(b + diff * 5 / 16)
                r, g, b = pixels[x + 1, y + 1][:3]
                pixels[x + 1, y + 1] = round(r + diff * 1 / 16), round(g + diff * 1 / 16), round(b + diff * 1 / 16)


__all__ = ["Dirs", "Mdl", "BlockGenerator", "ParticleGenerator"]
