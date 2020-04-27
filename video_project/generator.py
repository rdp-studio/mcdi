import logging
from PIL import Image

import cv2


def main_worker(fp, fps, *dirs):
    img_temp = Image.open(fp=dirs[0])
    width = img_temp.width
    height = img_temp.height
    del img_temp  # Detect image size

    logging.info("正在初始化“MJPG”视频编码器……")
    four_cc = cv2.VideoWriter_fourcc(*'MJPG')  # Initialize MJPG
    video_writer = cv2.VideoWriter(fp, four_cc, fps, (width, height))
    logging.info("正在渲染 %d 个帧。" % len(dirs))
    frame_count = 0  # Render starts
    for frame_path in dirs:
        frame = cv2.imread(frame_path)
        video_writer.write(frame)

        if frame_count % 50 == 0:  # Show progress
            logging.info("已渲染 %d 帧, 共计 %d 帧。" % (frame_count, len(dirs)))

        frame_count += 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    logging.critical("Never run this alone!")
