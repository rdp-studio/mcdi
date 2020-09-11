import itertools
from math import ceil

import cv2
import numpy as np


def count(__iterable):
    count = 0

    for i in __iterable:
        if i: count += 1

    return count


def ratio(__iterable):
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
            accum[y] = ratio(map(is_non_black_px, row)) > 0.5

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
            for i in range(5):
                yield (y := int(first_line + round(i * min_size / 4)))

    def find_extra_lines(self, ratio=1.5, *args, **kwargs):
        lines = list(
            self.find_lines(*args, **kwargs)
        )
        space_width = lines[1] - lines[0]

        if len(lines) > 5:
            max_find = (lines[5] - lines[4]) / ratio
        else:
            max_find = self.img.shape[0]

        valid_y = range(0, self.img.shape[0])

        line_sets = []

        for i in range(0, len(lines), 5):
            line_set = lines[i:i + 5]
            real_set = line_set.copy()

            for j in range(ceil(max_find / space_width)):
                extra_line = round(real_set[0] - space_width * j)

                if extra_line in valid_y and extra_line not in line_set:
                    line_set.append(extra_line)

            for j in range(ceil(max_find / space_width)):
                extra_line = round(real_set[-1] + space_width * j)

                if extra_line in valid_y and extra_line not in line_set:
                    line_set.append(extra_line)

            line_sets.append(line_set)

        return line_sets

    def find_valid_heads(self, factor=1.2, *args, **kwargs):
        line_sets = self.find_extra_lines(*args, **kwargs)

        for lines in line_sets:
            space_width = lines[1] - lines[0]  # 4 spaces

            img = self.img.copy()

            for y in lines:
                cv2.line(img, (0, y), (img.shape[1], y), (255, 0, 0))

            cv2.imshow("", img)
            cv2.waitKey()
            cv2.destroyAllWindows()

            img = self.img.copy()

            slice_count = 0

            for y in itertools.chain(lines, map(lambda x: round(x + space_width / 2), lines)):
                for x in range(0, self.img.shape[1]):
                    min_scan = int(round(y - space_width / 2))
                    max_scan = int(round(y + space_width / 2))

                    pixel_sums = []

                    for i in range(min_scan, max_scan):
                        pixel = self.img[y][x][:3]
                        pixel_sums.append(sum(pixel))

                    if not np.mean(pixel_sums):
                        slice_count += 1
                    elif space_width < slice_count < space_width * factor:
                        cv2.line(img, (x - slice_count, min_scan), (x - slice_count, max_scan), (0, 0, 255))
                        cv2.line(img, (x, min_scan), (x - slice_count, min_scan), (0, 0, 255))
                        cv2.line(img, (x, max_scan), (x - slice_count, max_scan), (0, 0, 255))
                        cv2.line(img, (x, min_scan), (x, max_scan), (0, 0, 255))
                        slice_count = 0
                    else:
                        slice_count = 0

            cv2.imshow("", img)
            cv2.waitKey()
            cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = Parser("staff.jpg")
    parser.find_valid_heads()
