import logging
import os
from enum import Enum
import time

from PIL import Image
from command_types import *

Directions = Enum("Directions", ("XY", "YZ", "XZ"))


class Generator(object):
    def __init__(self, fp, width=48, height=27, directions=Directions.XY, absolute=None, namespace="mcdi", func="vid"):
        logging.debug("Initializing generator...")
        logging.debug(f"Loading picture: {fp}.")
        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.directions = directions
        self.absolute = absolute
        self.built_function = Function(namespace, func)

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
                self.set_particle(x, y, pixel, 0.2, 1)

                if (built_count := x * self.y + y) % 1000 == 0:
                    logging.info("Built %s pixels, %s pixels in all." % (built_count, pixel_count))

        logging.info("Build process finished.")

    def set_particle(self, x, y, color, scale, count):
        r, g, b = color[:3]
        if self.directions == Directions.XY:
            if not self.absolute:
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 ~{x * scale} ~{(self.y - y - 1) * scale} ~ {scale / 4} {scale / 4} 0 1 {count} force")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 {x * scale + x_shift} {(self.y - y - 1) * scale + y_shift} {z_shift} {scale / 4} {scale / 4} 0 1 {count} force")
        elif self.directions == Directions.YZ:
            if not self.absolute:
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 ~ ~{x * scale} ~{(self.y - y - 1) * scale} {scale / 4} {scale / 4} 0 1 {count} force")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 {z_shift} {x * scale + x_shift} {(self.y - y - 1) * scale + y_shift} 0 {scale / 4} {scale / 4} 1 {count} force")
        elif self.directions == Directions.XZ:
            if not self.absolute:
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 ~{x * scale} ~ ~{(self.y - y - 1) * scale} {scale / 4} {scale / 4} 0 1 {count} force")
            else:
                x_shift, y_shift, z_shift = self.absolute
                self.built_function.append(f"particle minecraft:dust {r / 255} {g / 255} {b / 255} 1 {x * scale + x_shift} {z_shift} {(self.y - y - 1) * scale + y_shift} {scale / 4} 0 {scale / 4} 1 {count} force")

    def write_func(self, *args, **kwargs):
        logging.info(f"Writing {len(self.built_function)} command(s) built.")
        self.built_function.write(*args, **kwargs)
        logging.info("Write process finished.")


if __name__ == '__main__':
    PICS_PATH = r"D:\视频\Frames"  # Where you save your picture files.

    GAME_DIR = r"D:\Minecraft\.minecraft\versions\1.15.2"  # Your game directory
    WORLD_NAME = r"Template"  # Your world name

    WIDTH, HEIGHT = 96, 54

    FRAME_RATE = 30

    for pic_path in os.listdir(PICS_PATH):
        timestamp = time.time()
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        if os.path.isfile(pic_path := os.path.join(PICS_PATH, pic_path)):
            gen = Generator(os.path.join(PICS_PATH, pic_path), width=WIDTH, height=HEIGHT, absolute=(100, 5, 100))
            gen.build_pixels()
            gen.write_func(os.path.join(GAME_DIR, "saves", WORLD_NAME))
            while time.time() - timestamp < 1 / FRAME_RATE:
                time.sleep(1 / 120)
