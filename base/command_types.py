import os

class Function(list):
    def __init__(self, namespace="mcdi", func="func"):
        super().__init__()
        self.identifier = namespace, func

    def write(self, wp, limitation=None):
        namespace, func = self.identifier

        if not os.path.exists(wp):
            raise FileNotFoundError("World path or Minecraft path does not exist!")
        os.makedirs(os.path.join(wp, f"datapacks\\MCDI\\data\\{namespace}\\functions"), exist_ok=True)
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:  # Initialize package
            file.write('{"pack":{"pack_format":2333,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')

        with open(os.path.join(wp, f"datapacks\\MCDI\\data\\{namespace}\\functions\\{func}.mcfunction"), "w") as file:
            file.writelines(self[:limitation])  # Within the limitation

    def read(self, file_path):
        with open(file_path, "r") as file:
            self.extend(file.readlines())

    def append(self, _T: object) -> None:
        super().append(f"{_T}\n")
