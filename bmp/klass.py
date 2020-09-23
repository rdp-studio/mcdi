import logging

from PIL import Image

from base.minecraft_types import *


class BaseGenerator(object):
    def __init__(self, fp, width=256, height=144, namespace="mcdi", func="bmp"):
        logging.info(f"Initializing. Loading bitmap: {fp}.")

        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.built_function = Function(namespace, func)

    def write_datapack(self, *args, **kwargs):
        logging.info(f"Writing {len(self.built_function)} command(s) built.")
        self.built_function.to_pack(*args, **kwargs)
        logging.info("Write procedure finished.")
