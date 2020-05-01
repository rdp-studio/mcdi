class Progress(object):
    __author__ = "kworker"
    __doc__ = """Show a progress bar"""

    def __init__(self, pk=0, text="kworker", color="yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator):
        self.end_tick = generator.loaded_msgs[-1]["tick"]
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
    __doc__ = """Show some particles"""

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
    __doc__ = """Using falling blocks to show a piano fall"""

    def __init__(self, front_tick=90, summon_height=100, note_shift=0, front_shift=1, reversed=False, sustain=False):
        self.front_tick = front_tick
        self.sum_y = summon_height
        self.note_shift = note_shift
        self.front_shift = front_shift
        self.reversed = reversed
        self.sustain = sustain
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
                               generator.loaded_msgs))
        if self.sustain:  # Sustained only
            self.sustain_notes.extend(on_notes)
            for off_note in filter(lambda x: x["type"] == "note_off" and x["tick"] == generator.tick + self.front_tick,
                                   generator.loaded_msgs):
                map(lambda end_note: self.sustain_notes.remove(end_note),
                    filter(
                        lambda x: x["ch"] == off_note["ch"] and x["note"] == off_note["note"], self.sustain_notes
                    ))

        mapping = ["red", "orange", "yellow", "lime", "light_blue", "purple", "magenta", "pink"] * 4

        if self.sustain:  # Sustained only
            on_notes.extend(self.sustain_notes)
        for on_note in on_notes:
            block_name = f'{mapping[on_note["ch"] - 1]}_stained_glass'
            if self.reversed:
                note_shift = 128 - (on_note["note"] - self.note_shift)
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + note_shift} ~' \
                             f'{self.sum_y - generator.y_index} ~{-generator.wrap_index - 1 - self.front_shift} ' \
                             f'{{BlockState: {{Name: \\\"{block_name}\\\"}}, Time: 1, CustomName: ' \
                             f'\'\\\"{generator.tick}\\\"\'}}'
            else:
                max_tick = generator.loaded_msgs[-1]["tick"]
                wrap_sum = max_tick // generator.wrap_length + 1
                note_shift = on_note["note"] - self.note_shift
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + note_shift} ~' \
                             f'{self.sum_y - generator.y_index} ' \
                             f'~{wrap_sum - generator.wrap_index + 1 + self.front_shift}' \
                             f' {{BlockState: {{Name: \\\"{block_name}\\\"}}, Time: 1, CustomName:' \
                             f'\'\\\"{generator.tick}\\\"\'}}'
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=summon_cmd)
            generator.y_index += 1


from json import dumps


class Title(object):
    __author__ = "kworker"
    __doc__ = """Using title command to show some titles"""

    def __init__(self, titles):
        self.titles = titles

    def exec(self, generator):
        if not hasattr(self, "end_tick"):
            self.end_tick = generator.loaded_msgs[-1]["tick"]

        this_titles = list(filter(
            lambda x: (x["tick"] == generator.tick) if x["tick"] >= 0 else (
                    x["tick"] == generator.tick - self.end_tick + 1),
            self.titles
        ))

        for this_title in this_titles:
            del this_title["tick"]
            title_type = this_title["type"]
            del this_title["type"]

            json = dumps(this_title, ensure_ascii=False).replace('"', '\\"')
            title_cmd = f"title @a {title_type} {json}"
            generator.set_cmd_block(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index, command=title_cmd)
            generator.y_index += 1
