__author__ = "kworker"
__doc__ = """我只是一个简单的进度条。"""


class MainObject(object):
    def __init__(self, pk=0, name="Copyright (c) 2020 kworker", color="yellow", *args, **kwargs):
        self.pk = pk
        self.name = name
        self.color = color

    def execute(self, generator):
        if not hasattr(self, "max_tick"):
            self.max_tick = generator.parsed_msgs[-1]["tick"] - 1
        if generator.tick == 0:
            cmd = f"bossbar add {self.pk} {{\\\"text\\\": \\\"{self.name}\\\"}}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} color {self.color}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} max {self.max_tick}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} players @a"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} visible true"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            return None
        if generator.tick == self.max_tick:
            cmd = f"bossbar set {self.pk} visible false"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            return None
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command=f"bossbar set {self.pk} value {generator.tick}")
        generator.y_index += 1
