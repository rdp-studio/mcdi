import logging
import os

class Pos(float):
    def __str__(self):
        return super().__str__()

class RelPos(object):
    def __init__(self, pos):
        self.offset = pos

    def __str__(self):
        return f"~{self.offset}"

class LocalPos(object):
    def __init__(self, pos):
        self.offset = pos

    def __str__(self):
        return f"^{self.offset}"


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

    def append(self, _T: object) -> None:
        if hasattr(_T, "__str__"):
            if command := str(_T).endswith("\n"):
                super().append(command)
            else:
                super().append(f"{_T}\n")
        else:
            raise ValueError("Cannot add a object without attribute __str__ to a function.")

class Command(object):
    args = ()
    base = None

    def __str__(self):
        return f"{self.base} {' '.join(self.args)}"

class Particle(Command):
    base = "particle"

    def __init__(self, name, x=RelPos(0), y=RelPos(0), z=RelPos(0), dx=0, dy=0, dz=0, speed=0, count=0):
        self.args = name, x, y, z, dx, dy, dz, speed, count
