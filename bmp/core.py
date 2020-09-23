import enum
import math

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


class Directions(enum.Enum):
    XY = 0
    YZ = 1
    XZ = 2


class Model(enum.Enum):
    RGB = 0
    HSV = 1


class BlockGenerator(BaseGenerator):
    def __init__(self, mappings, directions=Directions.XY, absolute=None, model=Model.RGB, *args, **kwargs):
        super(BlockGenerator, self).__init__(*args, **kwargs)

        self.mappings = mappings
        self.absolute = absolute
        self.directions = directions
        self.model = model

    def build_pixels(self, resample=Image.LANCZOS):
        if self.img.width != self.x and self.img.height != self.y:
            logging.info(f"Resizing the picture to {self.x}x{self.y}.")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:
            logging.info("Resampleing is not required. Continue.")

        logging.info(f"Loading {(pixel_count := self.x * self.y)} pixels.")
        pixels = self.img.load()

        logging.info(f"Building {pixel_count} pixels loaded.")

        for x in range(self.x):
            for y in range(self.y):
                pixel = pixels[x, y]
                nearest_item = None
                minimums = 255 * 3 + 1
                for mapping in self.mappings:
                    for item in mapping:  # Calculates the difference
                        if self.model == Model.RGB:
                            color = item["color"]
                            r_diff = abs(color[0] - pixel[0])
                            g_diff = abs(color[1] - pixel[1])
                            b_diff = abs(color[2] - pixel[2])
                            diff = r_diff + g_diff + b_diff
                        elif self.model == Model.HSV:
                            c_h, c_s, c_v = rgb2hsv(*item["color"])
                            p_h, p_s, p_v = rgb2hsv(*pixel[:3])
                            h_diff = abs(c_h - p_h) / 360 * 255
                            s_diff = abs(c_s - p_s) * 255
                            v_diff = abs(c_v - p_v) * 255
                            diff = h_diff + s_diff + v_diff
                        else:
                            raise TypeError(f"Unknown color model: {self.model}")
                        if diff < minimums:
                            minimums = diff
                            nearest_item = item
                block_name = nearest_item["block"]
                self.set_block(x, y, block_name)

                if (built_count := x * self.y + y) % 1000 == 0:
                    logging.info("Built %s pixels, %s pixels in all." % (built_count, pixel_count))

        logging.info("Build procedure finished.")

    def set_block(self, x, y, block):
        if self.directions == Directions.XY:
            if not self.absolute:
                self.built_function.append(f"setblock ~{x} ~{self.y - y - 1} ~ minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(
                    f"setblock {x + x_shift} {self.y - y - 1 + y_shift} {z_shift} minecraft:{block} replace"
                )
        elif self.directions == Directions.YZ:
            if not self.absolute:
                self.built_function.append(f"setblock ~ ~{x} ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(
                    f"setblock {z_shift} {x + x_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace"
                )
        elif self.directions == Directions.XZ:
            if not self.absolute:
                self.built_function.append(f"setblock ~{x} ~ ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(
                    f"setblock {x + x_shift} {z_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace"
                )
