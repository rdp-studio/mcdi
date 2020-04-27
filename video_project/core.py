"""
Requirements:
Python 3.8.x
- Package: opencv-python
- Package: pillow
Minecraft 1.15.x
"""

import logging
import os
import time

from pic_project.core import Generator as Gen
from pic_project.core import concrete_mapping, wool_mapping, terracotta_mapping, Directions
from video_project import unattended, video_gen

PIC_DIRS = r"D:\revenge-frames"  # Where you save your image frame files, THAT MUST BE ASCII!!

GAME_DIR = r"D:\Minecraft\.minecraft\versions\1.15.2"  # Your game directory
WORLD_DIR = r"Template"  # Your world name
DATA_DIR = os.path.join(GAME_DIR, "saves", WORLD_DIR)  # NEVER CHANGE THIS

FROM = -1  # Useful when you suddenly lost your works
# Set it below 0 to activate auto mode.

UNATTENDED = True  # Whether you want to use operator or not
# <!-- These won't work unless you set UNATTENDED to True.
WAIT_TIME = 3  # The time to wait for the game to reload the picture.
# -->

VIDEO_GENERATE = True  # Whether you want to use generator or not, needs opencv-python
# <!-- These won't work unless you set VIDEO_GENERATE to True.
TEMP_DIR = r"D:\tmp"  # Where to save the temporary files, THAT MUST BE ASCII!!
GENERATE_DIR = r"D:\revenge.avi"  # Where to save the output
FPS = 24  # The expecting frame rate


# -->


class Generator(object):
    def __init__(self, fp, width=256, height=144, from_=0, unattended=True, video_generate=True,
                 mappings=None, directions=Directions.XY, absolute=True, tp=r"D:\tmp",
                 op="D:\\", fps=24, wait_time=3):
        logging.debug("Initializing...")  # Initialize
        self.fp = fp
        self.width = width
        self.height = height
        # <!-- from which frame, can be auto
        if from_ < 0:  # Override
            self.from_ = len(os.listdir(tp))
        else:  # Just continue
            self.from_ = from_
        # --> <!-- mappings, you can add more if you want
        if mappings is None:  # Override
            self.mappings = [concrete_mapping, wool_mapping, terracotta_mapping]
        else:
            self.mappings = mappings
        # --> <!-- normally not changed
        self.directions = directions
        self.absolute = absolute
        # --> <!-- only for video generate
        self.video_generate = video_generate
        self.tp = tp
        self.op = op
        self.fps = fps
        # --> <!-- only for unattended
        self.unattended = unattended
        self.wait_time = wait_time
        # -->

    def build_write_frames(self, wp):
        logging.info("Iterating the source directory...")

        frames = list()  # Iterate in the frames' directory
        for root, _, files in os.walk(PIC_DIRS):
            for frame_name in files:
                frames.append(os.path.join(root, frame_name))

        logging.info(f"Building {len(frames)} frames got.")

        frame_count = 0  # Counter
        flags = {"enabled": True, "done": False}
        if self.unattended:  # Create unattended thread
            unattended.main_worker(flags, self.wait_time, self.tp)

        for frame_path in frames:
            if frame_count < self.from_:  # If it's already created,
                logging.warning(f"Skipped {frame_count} frame(s).")
                frame_count += 1
                continue  # Skip this frame
            gen = Gen(frame_path, width=self.width, height=self.height, mappings=self.mappings,
                      directions=self.directions, absolute=self.absolute)

            logging.info(f"Built {frame_count} frame(s), {len(frames)} frames in all.")
            gen.build_pixels()
            logging.info(f"Wrote {frame_count} frame(s), {len(frames)} frames in all.")
            gen.write_built(wp)  # Calls pic_project.core, generates picture function

            flags["done"] = True  # Wake operator up
            logging.info("Waiting for the unattended process (if exists)...")
            while flags["done"] and self.unattended:
                pass  # Wake for the game
            if not self.unattended:  # Manual operation
                time.sleep(self.wait_time)

            frame_count += 1
        flags["enabled"] = False  # Stop unattended thread

        if self.video_generate:  # Create generate thread
            logging.info("Waiting for the video generator...")
            frames = list()  # Iterate in the temporary directory
            for root, _, files in os.walk(self.tp):
                for frame_name in files:
                    frames.append(os.path.join(root, frame_name))
            video_gen.main_worker(self.op, self.fps, *frames)

        logging.info("Build process finished.")  # Finish!


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    g = Generator(PIC_DIRS, width=256, height=144, unattended=UNATTENDED, video_generate=VIDEO_GENERATE,
                  tp=TEMP_DIR, op=GENERATE_DIR, from_=FROM, fps=FPS, wait_time=WAIT_TIME)
    g.build_write_frames(DATA_DIR)
