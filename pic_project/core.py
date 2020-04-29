"""
Requirements:
Python 3.8.x
- Package: pillow
Minecraft 1.15.x
"""

import logging
import os
from enum import Enum, unique

from PIL import Image

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")


# <!-- NEVER CHANGE THESE
@unique
class Types(Enum):
    COLORFUL = "color"
    NORMAL = "normal"


@unique
class Directions(Enum):
    XY = 0
    XZ = 1
    YZ = 2


# -->

PIC_DIR = r"D:\Frank.jpg"  # Where you save your picture file.

GAME_DIR = r"D:\Minecraft\.minecraft\versions\1.15.2"  # Your game directory
WORLD_DIR = r"Template"  # Your world name
DATA_DIR = os.path.join(GAME_DIR, "saves", WORLD_DIR)  # NEVER CHANGE THIS

# <!-- NEVER CHANGE THESE
color_index = [
    "white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray",
    "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"
]

concrete_mapping = {
    "type": Types.COLORFUL,
    "key": "concrete",
    "mapping": [
        (205, 210, 211), (222, 97, 1), (166, 47, 157), (36, 136, 198),
        (239, 174, 21), (92, 166, 24), (210, 99, 140), (53, 56, 60),
        (124, 124, 114), (21, 118, 134), (100, 32, 155), (43, 45, 141),
        (94, 58, 31), (72, 90, 36), (141, 34, 34), (9, 11, 16),
    ]}

wool_mapping = {
    "type": Types.COLORFUL,
    "key": "wool",
    "mapping": [
        (227, 231, 23), (246, 117, 44), (208, 77, 184), (48, 188, 222),
        (248, 193, 65), (95, 184, 53), (249, 169, 168), (62, 67, 70),
        (134, 134, 126), (0, 138, 143), (147, 54, 187), (58, 49, 144),
        (106, 66, 43), (80, 109, 41), (153, 43, 41), (22, 22, 26),
    ]}

terracotta_mapping = {
    "type": Types.COLORFUL,
    "key": "terracotta",
    "mapping": [
        (208, 177, 159), (161, 84, 47), (150, 86, 106), (116, 106, 134),
        (180, 130, 50), (99, 115, 58), (162, 79, 79), (61, 45, 41),
        (134, 106, 98), (85, 90, 90), (119, 70, 84), (76, 59, 88),
        (79, 54, 42), (74, 82, 47), (146, 64, 51), (43, 30, 24),
    ]}


# -->


class Generator(object):
    def __init__(self, fp, width=192, height=128, mappings=None, directions=Directions.XY, absolute=False):
        logging.debug("Initializing...")  # Initialize
        if mappings is None:  # Override
            self.mappings = [concrete_mapping]
        else:
            self.mappings = mappings
        logging.debug(f"Loading picture: {fp}")
        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.directions = directions
        self.absolute = absolute
        self.built_cmds = list()

    def build_pixels(self, resample=Image.LANCZOS):
        if self.img.width != self.x and self.img.height != self.y:
            logging.info("Resizing the picture...")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:  # Size is the same, no scale
            logging.info("No resize needed. Continue...")
        logging.info(f"Reading {(pixel_count := self.x * self.y)} pixels...")
        loaded_pixels = self.img.load()  # Load pixels
        logging.info(f"Building {pixel_count} pixels according to the mapping(s)...")
        for x in range(self.x):
            for y in range(self.y):
                pixel = loaded_pixels[x, y]
                nearest_color = None
                nearest_mapping = None
                minimums = 765  # The max possible value
                for mapping in self.mappings:
                    for color in mapping["mapping"]:
                        r_diff = abs(color[0] - pixel[0])
                        g_diff = abs(color[1] - pixel[1])
                        b_diff = abs(color[2] - pixel[2])
                        diff = r_diff + g_diff + b_diff
                        if diff < minimums:  # If this one is closer
                            minimums = diff
                            nearest_color = color
                            nearest_mapping = mapping
                if nearest_mapping["type"] == Types.COLORFUL:  # If it's colorful block
                    color = color_index[nearest_mapping["mapping"].index(nearest_color)]
                    _class = nearest_mapping["key"]
                    block_name = "%s_%s" % (color, _class)
                elif nearest_mapping["type"] == Types.NORMAL:  # If it's normal block
                    block_name = nearest_mapping["mapping"][nearest_color]
                self.set_block(x, y, block_name)  # Execute setblock builder

                if (built_count := x * self.y + y) % 4000 == 0:  # Show progress
                    logging.info("Built %s pixels, %s pixels in all." % (built_count, pixel_count))

        logging.info("Build process complete.")

    def set_block(self, x, y, block):
        if self.directions == Directions.XY:
            if not self.absolute:
                self.built_cmds.append("setblock ~{} ~{} ~ minecraft:{} replace\n".format(x, self.y - y - 1, block))
            else:
                self.built_cmds.append("setblock {} {} 0 minecraft:{} replace\n".format(x, self.y - y - 1, block))
        elif self.directions == Directions.YZ:
            if not self.absolute:
                self.built_cmds.append("setblock ~ ~{} ~{} minecraft:{} replace\n".format(x, self.y - y - 1, block))
            else:
                self.built_cmds.append("setblock  {} {} minecraft:{} replace\n".format(x, self.y - y - 1, block))
        elif self.directions == Directions.XZ:
            if not self.absolute:
                self.built_cmds.append("setblock ~{} ~ ~{} minecraft:{} replace\n".format(x, self.y - y - 1, block))
            else:
                self.built_cmds.append("setblock {} 0 {} minecraft:{} replace\n".format(x, self.y - y - 1, block))

    def write_built(self, wp):
        logging.info(f"Writing {(length := len(self.built_cmds))} command(s) built.")
        if length >= 65536:
            logging.warning("Notice: please try this command as your picture function is longer than 65536 line(s).")
            logging.info("Try this: /gamerule maxCommandChainLength %d" % (length + 1))  # Too long

        os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions"), exist_ok=True)
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions\picture.mcfunction"), "w") as file:
            file.writelines(self.built_cmds)
        logging.info("Write process finished.")
        logging.debug("To run the picture function: '/reload'")
        logging.debug("Then: '/function mcdi:music'")


if __name__ == '__main__':
    gen = Generator(PIC_DIR, mappings=[
        concrete_mapping,
        wool_mapping,
        terracotta_mapping,
    ], width=256, height=144)
    gen.build_pixels()
    gen.write_built(DATA_DIR)
