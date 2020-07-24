from typing import *


def list_to_char(pixel_list: List[int]):
    pixel_list[3], pixel_list[4], pixel_list[5], pixel_list[6] = \
        pixel_list[4], pixel_list[5], pixel_list[6], pixel_list[3]
    unicode_index = 0x2800  # Blind charset starts from U+2800
    for i, j in enumerate(pixel_list):  # For each pixel value:
        unicode_index += (1 << i) if j else 0  # List to byte algorithm
    return chr(unicode_index)


if __name__ == '__main__':
    print(list_to_char([1, 0, 1, 0, 0, 1, 0, 1]))
