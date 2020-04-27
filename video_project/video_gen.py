import logging

import cv2
from PIL import Image


def main_worker(fp, fps, *dirs):
    img_temp = Image.open(fp=dirs[0])
    width = img_temp.width
    height = img_temp.height
    del img_temp  # Detect image size

    logging.info("Initializing MJPG...")
    four_cc = cv2.VideoWriter_fourcc(*'MJPG')  # Initialize MJPG
    video_writer = cv2.VideoWriter(fp, four_cc, fps, (width, height))
    logging.info(f"Rendering {len(dirs)} frame(s)...")
    frame_count = 0  # Render starts
    for frame_path in dirs:
        frame = cv2.imread(frame_path)
        video_writer.write(frame)

        if frame_count % 50 == 0:  # Show progress
            logging.info(f"Rendered {frame_count} frame(s), {len(dirs)} frames in all.")

        frame_count += 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    logging.critical("Never run this alone!")
