import json
import os


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

    def to_pack(self, world_path, limitation=None, *args, **kwargs) -> None:
        """
        Write the function to a datapack.
        :param world_path:  The path of your world
        :param limitation:  The maximum length of the function
        :param args:        Passed to the file writer
        :param kwargs:      Passed to the file writer
        """
        if not os.path.exists(world_path):
            raise FileNotFoundError("World path or Minecraft path does not exist!")

        pack_path = os.path.join(world_path, f"datapacks\\MCDI\\data\\{self.namespace}\\functions")
        os.makedirs(pack_path, exist_ok=True)  # Create package

        meta_path = os.path.join(world_path, f"datapacks\\MCDI\\pack.mcmeta")
        with open(meta_path, "w", encoding="utf8") as file:  # Initialize - create and write pack.mcmeta
            file.write(json.dumps(self.__mcmeta))

        func_path = os.path.join(pack_path, f"{self.identifier}.mcfunction")
        with open(func_path, "w", encoding="utf8", *args, **kwargs) as file:  # Pack - create and write function file
            file.writelines(self[:limitation])

    def to_file(self, file_path, *args, **kwargs) -> None:
        """
        Write the function to a file.
        :param file_path:   The path of your function
        :param limitation:  The maximum length of the function
        :param args:        Passed to the file writer
        :param kwargs:      Passed to the file writer
        """
        with open(file_path, "w", encoding="utf8", *args, **kwargs) as file:  # Pack - create and write function file
            file.writelines(self)

    def from_file(self, file_path, *args, **kwargs) -> None:
        """
        Read a function from a file.
        :param file_path:   The path of your function
        :param limitation:  The maximum length of the function
        :param args:        Passed to the file writer
        :param kwargs:      Passed to the file writer
        """
        with open(file_path, "r", encoding="utf8", *args, **kwargs) as file:  # Unpack - read and load function file
            super().extend(file.readlines())

    def append(self, command) -> None:
        super().append(f"{command}\n")

    def extend(self, commands) -> None:
        for i in commands: self.append(i)
