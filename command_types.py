import logging
import os

class Function(list):
    def __init__(self, namespace="mcdi", func="func"):
        super().__init__()
        self.id = namespace, func

    def write(self, wp, limitation=None):
        namespace, func = self.id
        if (length := len(self)) >= 65536:
            logging.warning("Notice: please try this command as your function is longer than 65536 lines.")
            logging.warning("Try this: /gamerule maxCommandChainLength %d" % (length + 1))  # Too long

        if os.path.exists(wp):
            os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\%s\functions" % namespace), exist_ok=True)
        else:
            raise FileNotFoundError("World path or Minecraft path does not exist!")
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\%s\functions\%s.mcfunction" % (namespace, func)), "w") as file:
            file.writelines(self[:limitation])

    def read(self, file_path):
        with open(file_path, "r") as file:
            self.extend(file.readlines())

    def append(self, _T: object) -> None:
        if hasattr(_T, "__str__"):
            if (command := str(_T)).endswith("\n"):
                super().append(command)
            else:
                super().append(f"{_T}\n")
        else:
            raise ValueError("Cannot add a object without attribute __str__ to a function.")
