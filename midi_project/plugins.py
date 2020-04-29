class Progress(object):
    __author__ = "kworker"
    __doc__ = """A simple progressbar that's enough."""

    def __init__(self, pk=0, text="Copyright (c) 2020 kworker", color="yellow", *args, **kwargs):
        self.pk = pk
        self.text = text
        self.color = color

    def read(self, generator):
        if not hasattr(self, "max_tick"):
            self.end_tick = 0
            for msg in generator.parsed_msgs:
                if (t := msg["tick"]) > self.end_tick:
                    self.end_tick = t
        if generator.tick == 0:
            cmd = f"bossbar add {self.pk} {{\\\"text\\\": \\\"{self.text}\\\"}}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} color {self.color}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            cmd = f"bossbar set {self.pk} max {self.end_tick}"
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
        if generator.tick == self.end_tick:
            cmd = f"bossbar set {self.pk} visible false"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=cmd)
            generator.y_index += 1
            return None
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command=f"bossbar set {self.pk} value {generator.tick}")
        generator.y_index += 1


class Lightning(object):
    __author__ = "kworker"
    __doc__ = """君指先跃动の光は、私の一生不変の信仰に、唯私の超电磁炮永生き！"""

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def read(generator):
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                       command="summon lightning_bolt")
        generator.y_index += 1
