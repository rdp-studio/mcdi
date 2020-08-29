import json
import os
import warnings
from typing import *


class Function(list):
    __mcmeta = {
        "pack": {
            "pack_format": 2333,
            "description": "Made by MCDI, a project by kworker(FrankYang)."
        }
    }

    def __init__(self, namespace="mcdi", identifier="func"):
        super().__init__()
        self.namespace = namespace
        self.identifier = identifier

    def to_pack(self, world_path, limitation=None) -> None:
        """
        Write the function to a datapack.
        :param world_path:  The path of your world
        :param limitation:  The maximum func length
        """
        if not os.path.exists(world_path):
            raise FileNotFoundError("World path or Minecraft path does not exist!")

        pack_path = os.path.join(world_path, f"datapacks\\MCDI\\data\\{self.namespace}\\functions")
        os.makedirs(pack_path, exist_ok=True)  # Create package

        meta_path = os.path.join(world_path, f"datapacks\\MCDI\\pack.mcmeta")
        with open(meta_path, "w", encoding="utf8") as file:  # Initialize - create and write pack.mcmeta
            file.write(json.dumps(self.__mcmeta))

        func_path = os.path.join(pack_path, f"{self.identifier}.mcfunction")
        with open(func_path, "w", encoding="utf8") as file:  # Pack - create and write function file
            file.writelines(self[:limitation])

    def to_file(self, file_path, limitation=None) -> None:
        """
        Write the function to a file.
        :param file_path:   The path of your function
        :param limitation:  The maximum func length
        """
        with open(file_path, "w", encoding="utf8") as file:  # Pack - create and write function file
            file.writelines(self[:limitation])

    def from_file(self, file_path) -> None:
        """
        Read a function from a file.
        :param file_path:   The path of your function
        :param limitation:  The maximum func length
        """
        with open(file_path, "r", encoding="utf8") as file:  # Unpack - read and load function file
            super().extend(file.readlines())

    def append(self, command) -> None:
        super().append(f"{command}\n")

    def extend(self, commands) -> None:
        for i in commands: self.append(i)

    def insert(self, __index, command):
        super().insert(__index, f"{command}\n")


class TagCompound(dict):
    def __str__(self):
        string = "{"
        for key, value in self.items():
            string += f"{key}:"
            if isinstance(value, TagByte):
                string += f"{value}b"
            elif isinstance(value, TagShort):
                string += f"{value}s"
            elif isinstance(value, (TagInt, int)):
                string += f"{value}"
            elif isinstance(value, TagLong):
                string += f"{value}l"
            elif isinstance(value, (TagFloat, float)):
                string += f"{value}f"
            elif isinstance(value, TagDouble):
                string += f"{value}d"
            elif isinstance(value, (TagByteArray, TagIntArray, TagLongArray)):
                string += f"{value}"
            elif isinstance(value, (TagString, str)):
                string += f'"{value}"'
            elif isinstance(value, (TagList, list)):
                string += f"{value}"
            elif isinstance(value, (TagCompound, dict)):
                string += f"{value}"
            string += ","
        string = string.rstrip(",")
        return string + "}"


class TagByte(int):
    def __init__(self, value: Union[bytes, int, float]):
        if isinstance(value, bytes):
            value = int.from_bytes(value, "big")
        elif isinstance(value, float):
            value = round(value)  # No int, round
        if -128 < value < 127:
            raise OverflowError("Invalid value: value not in byte(int_8) range!")

        super().__init__(value)


class TagShort(int):
    def __init__(self, value: Union[bytes, int, float]):
        if isinstance(value, bytes):
            value = int.from_bytes(value, "big")
        elif isinstance(value, float):
            value = round(value)  # No int, round
        if -32768 < value < 32767:
            raise OverflowError("Invalid value: value not in short(int_16) range!")

        super().__init__(value)


class TagInt(int):
    def __init__(self, value: Union[bytes, int, float]):
        if isinstance(value, bytes):
            value = int.from_bytes(value, "big")
        elif isinstance(value, float):
            value = round(value)  # No int, round
        if -2147483648 < value < 2147483647:
            raise OverflowError("Invalid value: value not in int(int_32) range!")

        super().__init__(value)


class TagLong(int):
    def __init__(self, value: Union[bytes, int, float]):
        if isinstance(value, bytes):
            value = int.from_bytes(value, "big")
        elif isinstance(value, float):
            value = round(value)  # No int, round
        if -9223372036854775808 < value < 9223372036854775807:
            raise OverflowError("Invalid value: value not in long(int_64) range!")

        super().__init__(value)


class TagFloat(float):
    def __init__(self, value: Union[int, float]):
        if -1.17549e-38 < value < 3.40282e+38:
            raise OverflowError("Invalid value: value not in C float range!")

        super().__init__(value)


class TagDouble(float):
    def __init__(self, value: Union[int, float]):
        if -2.22507e-308 < value < 1.79769e+308:
            raise OverflowError("Invalid value: value not in C double range!")

        super().__init__(value)


class TagByteArray(list):
    def __str__(self):
        string = "[B;"
        for value in self:
            if isinstance(value, TagByte):
                string += f"{value}"
            elif isinstance(value, bytes):
                string += f"{TagByte(value)}"
            else:
                raise ValueError("A TagByteArray can only handle TagByte or bytes objects.")
            string += ","
        string = string.rstrip(",")
        return string + "]"


class TagString(str):
    def __init__(self, value):
        if len(value) > 32767:
            raise OverflowError("Invalid value: too long string. Max: 32767.")

        super().__init__(value)


class TagList(list):
    def __str__(self):
        string = "["
        for value in self:
            if isinstance(value, TagByte):
                string += f"{value}b"
            elif isinstance(value, TagShort):
                string += f"{value}s"
            elif isinstance(value, (TagInt, int)):
                string += f"{value}"
            elif isinstance(value, TagLong):
                string += f"{value}l"
            elif isinstance(value, (TagFloat, float)):
                string += f"{value}f"
            elif isinstance(value, TagDouble):
                string += f"{value}d"
            elif isinstance(value, (TagByteArray, TagIntArray, TagLongArray)):
                string += f"{value}"
            elif isinstance(value, (TagString, str)):
                string += f'"{value}"'
            elif isinstance(value, (TagList, list)):
                string += f"{value}"
            elif isinstance(value, (TagCompound, dict)):
                string += f"{value}"
            string += ","
        string = string.rstrip(",")
        return string + "]"


class TagIntArray(list):
    def __str__(self):
        string = "[I;"
        for value in self:
            if isinstance(value, TagInt):
                string += f"{value}"
            elif isinstance(value, (bytes, int, float)):
                string += f"{TagInt(value)}"
            else:
                raise ValueError("A TagIntArray can only handle TagInt or int-like objects.")
            string += ","
        string = string.rstrip(",")
        return string + "]"


class TagLongArray(list):
    def __str__(self):
        string = "[L;"
        for value in self:
            if isinstance(value, TagLong):
                string += f"{value}"
            elif isinstance(value, (bytes, int, float)):
                string += f"{TagLong(value)}"
            else:
                raise ValueError("A TagLongArray can only handle TagLong or int-like objects.")
            string += ","
        string = string.rstrip(",")
        return string + "]"


NBT = TagCompound  # Alias
