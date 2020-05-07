import logging
import os
import threading
from time import sleep
from time import time as t

from PIL import ImageGrab


def main_function(flags, time, tmp):
    logging.info("Waiting for the generator...")  # Wait for the core
    while flags["enabled"]:
        while not flags["done"]:
            sleep(1E-2)
        logging.info("Waiting for the refresh...")
        sleep(time)  # Wait for the game
        logging.info("Grabbing screenshot...")
        im = ImageGrab.grab()  # Take screenshot
        im.save(os.path.join(tmp, "%d.png" % t()))
        logging.info("Continue for the next frame!")  # Continue!
        flags["done"] = False
    # Exit


def main_worker(flags, time, tmp):
    thread = threading.Thread(target=main_function, args=(flags, time, tmp))
    thread.setDaemon(daemonic=True) or thread.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    logging.critical("Never run this alone!")
