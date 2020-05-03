"""
Requirements:
Python 3.8.x
- Package: pillow
Minecraft 1.15.x
"""

import logging
import os
from enum import Enum

from PIL import Image

Directions = Enum("Directions", ("XY", "YZ", "XZ"))


class Generator(object):
    def __init__(self, fp, mappings, width=192, height=128, directions=Directions.XY, absolute=False):
        logging.debug("Initializing generator...")
        self.mappings = mappings
        logging.debug(f"Loading picture: {fp}.")
        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.directions = directions
        self.absolute = absolute
        self.built_commands = list()

    def build_pixels(self, resample=Image.LANCZOS):
        if self.img.width != self.x and self.img.height != self.y:
            logging.debug(f"Resizing the picture to {self.x}x{self.y}.")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:
            logging.debug("No resize needed. Continue...")
        logging.debug(f"Loading {(pixel_count := self.x * self.y)} pixels...")

        loaded_pixels = self.img.load()
        logging.info(f"Building {pixel_count} pixels loaded.")
        for x in range(self.x):
            for y in range(self.y):
                pixel = loaded_pixels[x, y]
                nearest_item = None
                minimums = 255 * 3 + 1
                for mapping in self.mappings:
                    for item in mapping:
                        color = item["color"]
                        r_diff = abs(color[0] - pixel[0])
                        g_diff = abs(color[1] - pixel[1])
                        b_diff = abs(color[2] - pixel[2])
                        diff = r_diff + g_diff + b_diff
                        if diff < minimums:
                            minimums = diff
                            nearest_item = item
                block_name = nearest_item["block"]
                self.set_block(x, y, block_name)

                if (built_count := x * self.y + y) % 4000 == 0:
                    logging.info("Built %s pixels, %s pixels in all." % (built_count, pixel_count))

        logging.info("Build process finished.")

    def set_block(self, x, y, block):
        if self.directions == Directions.XY:
            if not self.absolute:
                self.built_commands.append(f"setblock ~{x} ~{self.y - y - 1} ~ minecraft:{block} replace\n")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_commands.append(f"setblock {x + x_shift} {self.y - y - 1 + y_shift} {z_shift} "
                                           f"minecraft:{block} replace\n")
        elif self.directions == Directions.YZ:
            if not self.absolute:
                self.built_commands.append(f"setblock ~ ~{x} ~{self.y - y - 1} minecraft:{block} replace\n")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_commands.append(f"setblock {z_shift} {x + x_shift} {self.y - y - 1 + y_shift} "
                                           f"minecraft:{block} replace\n")
        elif self.directions == Directions.XZ:
            if not self.absolute:
                self.built_commands.append(f"setblock ~{x} ~ ~{self.y - y - 1} minecraft:{block} replace\n")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_commands.append(f"setblock {x + x_shift} {z_shift} {self.y - y - 1 + y_shift} "
                                           f"minecraft:{block} replace\n")

    def write_func(self, wp, namespace="mcdi", func="music"):
        logging.info(f"Writing {(length := len(self.built_commands))} command(s) built.")
        if length >= 65536:
            logging.warning("Notice: please try this command as your picture function is longer than 65536 line(s).")
            logging.warning("Try this: /gamerule maxCommandChainLength %d" % (length + 1))  # Too long

        if os.path.exists(wp):
            os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\%s\functions" % namespace), exist_ok=True)
        else:
            raise FileNotFoundError("World path or Minecraft path does not exist!")
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\%s\functions\%s.mcfunction" % (namespace, func)), "w") as file:
            file.writelines(self.built_commands)
        logging.info("Write process finished.")
        logging.debug("To run the picture function: '/reload'")
        logging.debug(f"Then: '/function {namespace}:{func}'")


if __name__ == '__main__':
    from json import loads
    with open("vanilla_blocks.json") as f:
        MAPPING = loads(f.read())

    PIC_PATH = r"D:\图片\mojave_dynamic_10.jpeg"  # Where you save your picture file.

    GAME_DIR = r"D:\Minecraft\.minecraft\versions\fabric-loader-0.8.2+build.194-1.14.4"  # Your game directory
    WORLD_NAME = r"Tester"  # Your world name

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    gen = Generator(PIC_PATH, mappings=[MAPPING])
    gen.build_pixels()
    gen.write_func(os.path.join(GAME_DIR, "saves", WORLD_NAME))
