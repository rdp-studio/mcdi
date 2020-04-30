class Progress(object):
    __author__ = "kworker"
    __doc__ = """A simple progressbar that's enough."""

    def __init__(self, pk=0, text="kworker", color="yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator):
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

    def __init__(self):
        pass

    @staticmethod
    def exec(generator):
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command="summon lightning_bolt")
        generator.y_index += 1


class Particle(object):
    __author__ = "kworker"
    __doc__ = """Show some fun particles"""

    def __init__(self, particle="end_rod", x_shift=0, y_shift=0, z_shift=0,
                 dx=0, dy=1, dz=0, speed=1, count=1, additional=()):
        self.particle = particle
        self.x_shift = x_shift
        self.y_shift = y_shift
        self.z_shift = z_shift
        self.args = (dx, dy, dz, speed, count)
        self.additional = additional
        pass

    def exec(self, generator):
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command=f"particle {self.particle} {' '.join(map(str, self.additional))} ~{self.x_shift}"
                                        f" ~{self.y_shift} ~{self.z_shift} {' '.join(map(str, self.args))} force")
        generator.y_index += 1


class PianoFall(object):
    __author__ = "kworker"
    __doc__ = """Using particles to show a piano waterfall"""

    def __init__(self, front_tick=90, sum_y=100, back_shift=0):
        self.front_tick = front_tick
        self.sum_y = sum_y
        self.back_shift = back_shift
        self.sustain_notes = []

    def exec(self, generator):
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command=f"execute as @e[name={generator.tick - self.front_tick},type=minecraft:falling_b"
                                        f"lock] at @s run particle minecraft:end_rod ~ ~ ~ 0.25 0.25 0.25 0.1 100 force")
        generator.y_index += 1
        generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index, z_shift=generator.wrap_index,
                                command=f"kill @e[name={generator.tick - self.front_tick},type=minecraft:falling_block]")
        generator.y_index += 1

        on_notes = list(filter(lambda x: x["type"] == "note_on" and x["tick"] == generator.tick + self.front_tick,
                               generator.parsed_msgs))
        off_notes = list(filter(lambda x: x["type"] == "note_off" and x["tick"] == generator.tick + self.front_tick,
                                generator.parsed_msgs))
        self.sustain_notes.extend(on_notes)
        for off_note in off_notes:
            end_notes = list(filter(lambda x: x["ch"] == off_note["ch"] and x["note"] == off_note["note"],
                                    self.sustain_notes))
            for end_note in end_notes:
                self.sustain_notes.remove(end_note)

        mapping = ["red", "orange", "yellow", "lime", "green", "cyan", "blue", "light_blue",
                   "purple", "magenta", "pink", "red", "orange", "yellow", "lime", "green"]

        on_notes.extend(self.sustain_notes)
        for on_note in on_notes:
            note_shift = 128 - (on_note["note"] - self.back_shift)
            block_name = f'{mapping[on_note["ch"] - 1]}_concrete'
            summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + note_shift} ~' \
                         f'{self.sum_y - generator.y_index} ~{-generator.wrap_index - 1} {{BlockState: {{' \
                         f'Name: \\\"{block_name}\\\"}}, Time: 1, CustomName: \'\\\"{generator.tick}\\\"\'}}'
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=summon_cmd)
            generator.y_index += 1
