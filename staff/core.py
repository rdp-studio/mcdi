import cv2
import numpy as np
import itertools
import matplotlib.pyplot as plt


def count(__iterable):
    count = 0

    for i in __iterable:
        if i: count += 1

    return count

def percent(__iterable):
    count = 0

    for j, i in enumerate(__iterable):
        if i: count += 1

    return count / (j + 1)

class Parser(object):
    def __init__(self, fp):
        self.img = cv2.imread(fp, cv2.IMREAD_UNCHANGED)

    def find_lines(self, minimum=64, maximum=192, size_x=32, size_y=16, threshold=1):
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, minimum, maximum)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, minLineLength=50, maxLineGap=10)[:, 0, :]

        accum = [
            0 for i in range(len(self.img))
        ]

        image = np.ndarray(self.img.shape)

        for x1, y1, x2, y2 in lines:
            if abs(y1 - y2) > 10:  # Too tilt
                continue
            if abs(x1 - x2) < 10:  # Too short
                continue
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255))

        kernel = np.ones((size_x, size_y), np.uint8, order="C")
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        is_non_black_px = lambda col: sum(col[:3]) > threshold

        for y, row in enumerate(image):  # Where lines are detected
            accum[y] = percent(map(is_non_black_px, row)) > 0.5

        region_sizes = []
        region_size = 0
        first_lines = []

        for i, value in enumerate(accum):
            if value and (not region_size):
                first_lines.append(i)

            region_size += value

            if not value:
                if region_size:  # It's a region
                    region_sizes.append(region_size)
                region_size = 0  # Reset region

        min_size = np.min(region_sizes)

        for first_line in first_lines:
            for i in range(5): yield int(first_line + round(i * min_size / 4))

    def find_heads(self, *args, **kwargs):
        lines = list(self.find_lines(*args, **kwargs))
        space_width = sum(lines) / 5  # 5 Lines -> 4 Spaces

        for y in lines:
            for x in range(0, self.img.shape[1]):
                min_scan = int(round(y - space_width / 2))
                max_scan = int(round(y + space_width / 2))

                pixel_sums = []

                for i in range(min_scan, max_scan):
                    pixel_sums.append(sum(self.img[y][x][:3]))

                if np.mean(pixel_sums) < 16:
                    NotImplemented
