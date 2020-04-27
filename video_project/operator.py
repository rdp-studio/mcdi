import logging
import threading
from time import sleep
from time import time as time_
import os

from PIL import ImageGrab


def main_function(flags, time, tmp):
    logging.info("正在等待生成器。")  # Wait for the core
    while flags["enabled"]:
        while not flags["done"]:
            sleep(1E-2)
        logging.info("正在等待游戏刷新。")
        sleep(time)  # Wait for the game
        logging.info("正在获取屏幕截图。")
        im = ImageGrab.grab()  # Take screenshot
        im.save(os.path.join(tmp, "%d.png" % time_()))
        logging.info("任务阻塞结束，进入下一帧。")  # Continue!
        flags["done"] = False
    # Exit


def main_worker(flags, time, tmp):
    thread = threading.Thread(target=main_function, args=(flags, time, tmp))
    thread.setDaemon(daemonic=True)
    thread.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    logging.critical("Never run this alone!")
