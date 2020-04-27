"""
Requirements:
Python 3.8.x
- Package: pillow
Minecraft 1.15.x
** An Nvidia graphics card **
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

PIC_DIR = r"D:\图片\Frank.jpg"  # Where you save your picture file.

GAME_DIR = r"D:\Minecraft\.minecraft\versions\1.15.2"  # Your game directory
WORLD_DIR = r"Test"  # Your world name
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
        logging.info("正在初始化生成器……")
        self.mappings = mappings
        if mappings is None:
            self.mappings = [concrete_mapping]
        logging.info("正在读取图片：%s。" % fp)
        self.img = Image.open(fp=fp)
        self.x = width
        self.y = height
        self.directions = directions
        self.absolute = absolute
        self.built_cmds = list()

    def build_pixels(self, resample=Image.LANCZOS):
        if self.img.width != self.x and self.img.height != self.y:
            logging.info("正在缩放图片……")
            self.img = self.img.resize((self.x, self.y), resample=resample)
        else:
            logging.info("图片的尺寸等于构建尺寸，不予缩放。")
        logging.info("正在加载图片中的 %d 个像素……" % (pixel_count := self.x * self.y))
        loaded_pixels = self.img.load()
        logging.info("按照映射表构建已读取的 %d 个像素……" % pixel_count)
        for x in range(self.x):
            for y in range(self.y):
                pixel = loaded_pixels[x, y]
                nearest_color = None
                nearest_mapping = None
                minimums = 765
                for mapping in self.mappings:
                    for color in mapping["mapping"]:
                        r_diff = abs(color[0] - pixel[0])
                        g_diff = abs(color[1] - pixel[1])
                        b_diff = abs(color[2] - pixel[2])
                        diff = r_diff + g_diff + b_diff
                        if diff < minimums:
                            minimums = diff
                            nearest_color = color
                            nearest_mapping = mapping
                if nearest_mapping["type"] == Types.COLORFUL:
                    color = color_index[nearest_mapping["mapping"].index(nearest_color)]
                    _class = nearest_mapping["key"]
                    block_name = "%s_%s" % (color, _class)
                elif nearest_mapping["type"] == Types.NORMAL:
                    block_name = nearest_mapping["mapping"][nearest_color]
                self.set_block(x, y, block_name)

                if (built_count := x * self.y + y) % 4000 == 0:
                    logging.info("已构建 %d 像素, 共计 %d 像素。" % (built_count, pixel_count))

        logging.info("构建像素完成。")

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
        logging.info("写入已构建的 %d 条指令。" % (length := len(self.built_cmds)))
        if length >= 65536:
            logging.warning("注意，由于您的图片函数长于默认允许的最大值（65536），请尝试键入以下指令。")
            logging.info("试试这个：/gamerule maxCommandChainLength %d" % (length + 1))

        os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions"), exist_ok=True)
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions\picture.mcfunction"), "w") as file:
            file.writelines(self.built_cmds)
        logging.info("写入指令完成。")
        logging.info("要运行图片函数，键入：'/reload'")
        logging.info("接着键入： '/function mcdi:picture'")


if __name__ == '__main__':
    gen = Generator(PIC_DIR, mappings=[
        concrete_mapping,
        wool_mapping,
        terracotta_mapping,
    ], width=256, height=144)
    gen.build_pixels()
    gen.write_built(DATA_DIR)
