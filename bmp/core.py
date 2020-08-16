import enum
import json
import logging
import math
from functools import reduce
from typing import *

from PIL import Image

from base.minecraft_types import Function


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


class BlockGenerator(object):
    def __init__(self, fp, mappings, width=256, height=144, directions=Directions.XY, absolute=None, model=Model.RGB,
                 namespace="mcdi", func="bmp"):
        logging.debug(f"Initializing. Loading bitmap: {fp}.")

        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.mappings = mappings
        self.absolute = absolute
        self.directions = directions
        self.model = model
        self.built_function = Function(namespace, func)

    def build_pixels(self, resample=Image.LANCZOS):
        if self.img.width != self.x and self.img.height != self.y:
            logging.debug(f"Resizing the picture to {self.x}x{self.y}.")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:
            logging.debug("No resize needed. Continue...")

        logging.debug(f"Loading {(pixel_count := self.x * self.y)} pixels...")
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
                    f"setblock {x + x_shift} {self.y - y - 1 + y_shift} {z_shift} minecraft:{block} replace")
        elif self.directions == Directions.YZ:
            if not self.absolute:
                self.built_function.append(f"setblock ~ ~{x} ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(
                    f"setblock {z_shift} {x + x_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace")
        elif self.directions == Directions.XZ:
            if not self.absolute:
                self.built_function.append(f"setblock ~{x} ~ ~{self.y - y - 1} minecraft:{block} replace")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(
                    f"setblock {x + x_shift} {z_shift} {self.y - y - 1 + y_shift} minecraft:{block} replace")

    def write_datapack(self, *args, **kwargs):
        logging.info(f"Writing {len(self.built_function)} command(s) built.")
        self.built_function.to_pack(*args, **kwargs)
        logging.info("Write procedure finished.")


class TextGenerator(object):
    def __init__(self, fp, width=256, height=144, namespace="mcdi", func="bmp"):
        logging.debug(f"Initializing. Loading bitmap: {fp}.")

        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.built_function = Function(namespace, func)

    def build_pixels(self, resample=Image.LANCZOS, use_dither=True):
        if self.img.width != self.x and self.img.height != self.y:
            logging.debug(f"Resizing the picture to {self.x}x{self.y}.")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:
            logging.debug("No resize needed. Continue...")

        logging.debug(f"Loading {(pixel_count := self.x * self.y)} pixels...")
        pixels = self.img.load()

        logging.info(f"Building {pixel_count} pixels loaded.")

        image_table = [[0 for j in range(self.img.width)] for i in range(self.img.height)]

        if use_dither:
            for y in range(1, self.img.height - 1):
                for x in range(1, self.img.width - 1):
                    old_pixel = pixels[x, y][:3]
                    pixel_val = round(sum(old_pixel) / 765) * 255
                    new_pixel = [pixel_val for _ in range(0, 3)]
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

        for x in range(self.img.width):  # For each pixel, transform to "pixels" syntax to build
            for y in range(self.img.height):
                image_table[y][x] = pixels[x, y][:3]

                if (built_count := x * self.y + y) % 1000 == 0:
                    logging.info("Built %s pixels, %s pixels in all." % (built_count, pixel_count))

        self.built_function.append(f"tellraw @a {self.pixels_to_char(image_table)}")

        logging.info("Build procedure finished.")

    @staticmethod
    def list_to_char(pixel_list: Iterable[int]):
        pixel_list = list(pixel_list)
        pixel_list[3], pixel_list[4], pixel_list[5], pixel_list[6] = \
            pixel_list[4], pixel_list[5], pixel_list[6], pixel_list[3]
        unicode_index = 0x2800  # Blind charset starts from U+2800
        for i, j in enumerate(pixel_list):  # For each pixel value:
            unicode_index += (1 << i) if j else 0  # List to byte algorithm
        return chr(unicode_index)

    @classmethod
    def pixels_to_char(cls, pixel_list: List[List[int]]):
        blocks, row_length, col_length = [], len(pixel_list), len(pixel_list[0])
        pixel_blocks = [
            [
                [
                    0 for _1 in range(8)
                ] for _2 in range(col_length // 2)
            ] for _3 in range(row_length // 4)
        ]

        for row_index, row in enumerate(pixel_list):
            for col_index, col in enumerate(row):
                outer_block_row = row_index // 4
                outer_block_col = col_index // 2
                inner_block = row_index % 4 + 4 * (col_index % 2)  # Character pattern
                pixel_blocks[outer_block_row][outer_block_col][inner_block] = col

        for row_index, row in enumerate(pixel_blocks):
            for col_index, col in enumerate(row):
                string = cls.list_to_char(map(lambda pixel: round(sum(pixel) / 765), col))
                r_avg = round(reduce(lambda x, y: (x[0] + y[0], 0, 0), col)[0] / 8)
                g_avg = round(reduce(lambda x, y: (0, x[1] + y[1], 0), col)[1] / 8)
                b_avg = round(reduce(lambda x, y: (0, 0, x[2] + y[2]), col)[2] / 8)
                color_string = "".join(
                    ("#",
                     color if len(color := hex(r_avg)[2:]) == 2 else "0" + color,
                     color if len(color := hex(g_avg)[2:]) == 2 else "0" + color,
                     color if len(color := hex(b_avg)[2:]) == 2 else "0" + color,
                     )
                )
                block = {"text": string, "color": color_string}
                blocks.append(block)

            blocks.append({"text": "\n"})

        return json.dumps(blocks, ensure_ascii=False)

    def write_datapack(self, *args, **kwargs):
        logging.info(f"Writing {len(self.built_function)} command(s) built.")
        self.built_function.to_pack(*args, **kwargs)
        logging.info("Write procedure finished.")


if __name__ == '__main__':
    pass
