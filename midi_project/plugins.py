from midi_project.core import Generator


class Plugin(object):
    def __init__(self):
        pass

    def exec(self, generator: Generator):
        pass

    def init(self, generator: Generator):
        pass


class Progress(object):
    __author__ = "kworker"
    __doc__ = """Simply shows a progress bar"""

    def __init__(self, pk: "The ID for the bossbar, no need to care for in most cases."=0,
                 text: "The title for the bossbar to show on the top."="MCDI",
                 color: "The color for the bossbar and the title."="yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator: Generator):
        if not hasattr(self, "end_tick"):
            self.end_tick = max(generator.loaded_messages, key=lambda x: x["tick"])["tick"]
        if generator.tick_count == 0:
            cmd = f'bossbar add {self.pk} {{"text": "{self.text}"}}'
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} color {self.color}"
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} max {self.end_tick}"
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} players @a"
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} visible true"
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            return None
        if generator.tick_count == self.end_tick:
            cmd = f"bossbar set {self.pk} visible false"
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=cmd):
                generator.y_index += 1
            return None
        if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                       z_shift=generator.wrap_index,
                                       command=f"bossbar set {self.pk} value {generator.tick_count}"):
            generator.y_index += 1


class PianoFall(object):
    __author__ = "kworker"
    __doc__ = """Shows a fancy piano fall"""

    def __init__(self, front_tick: "How many ticks should the blocks fall before the note plays."=90,
                 summon_height: "How high should the command blocks summon falling blocks."=100,
                 note_shift: "Moves the piano fall further away in build axis."=0,
                 front_shift: "Moves the piano fall further away in wrap axis."=1,
                 reversed: "The piano fall will be closer to the first command block instead of the last one."=False,
                 sustain: "Shows a long bar instead of a dot for long notes."=False,
                 die_commands: "Do the command(s) when a falling block dies." = (),
                 all_commands: "Do the command(s) for every falling block."=()):
        self.front_tick = front_tick
        self.sum_y = summon_height
        self.note_shift = note_shift
        self.front_shift = front_shift
        self.reversed = reversed
        self.sustain = sustain
        self.die_commands = die_commands
        self.all_commands = all_commands
        self.sustain_notes = []

    def init(self, generator: Generator):
        generator.blank_ticks += self.front_tick

    def exec(self, generator: Generator):
        for command in self.die_commands:
            generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                        z_shift=generator.wrap_index,
                                        command=f"execute as @e[name={generator.tick_count - self.front_tick},type="
                                                f"minecraft:falling_block] at @s run {command}")
            generator.y_index += 1
        for command in self.all_commands:
            generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                        z_shift=generator.wrap_index,
                                        command=f"execute as @e[type=minecraft:falling_block] at @s run {command}")
            generator.y_index += 1
        generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                    z_shift=generator.wrap_index,
                                    command=f"kill @e[name={generator.tick_count - self.front_tick},type=minecraft:falli"
                                            f"ng_block]")
        generator.y_index += 1

        on_notes = list(filter(lambda x: x["type"] == "note_on" and x["tick"] == generator.tick_count + self.front_tick,
                               generator.loaded_messages))
        if self.sustain:  # Sustained only
            self.sustain_notes.extend(on_notes)
            for off_note in filter(
                    lambda x: x["type"] == "note_off" and x["tick"] == generator.tick_count + self.front_tick,
                    generator.loaded_messages):
                map(
                    lambda end_note: self.sustain_notes.remove(end_note),
                    filter(lambda x: x["ch"] == off_note["ch"] and x["note"] == off_note["note"], self.sustain_notes)
                )

        mapping = ["red", "orange", "yellow", "lime", "light_blue", "purple", "magenta", "pink"] * 4

        if self.sustain:  # Sustained only
            on_notes.extend(self.sustain_notes)

        for on_note in on_notes:
            block_name = f'{mapping[on_note["ch"] - 1]}_stained_glass'
            if self.reversed:
                note_shift = 128 - (on_note["note"] - self.note_shift)
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + note_shift} ~' \
                             f'{self.sum_y - generator.y_index} ~{-generator.wrap_index - 1 - self.front_shift} ' \
                             f'{{BlockState: {{Name: "{block_name}"}}, Time: 1, CustomName: ' \
                             f'\'"{generator.tick_count}"\'}}'
            else:
                if not hasattr(self, "end_tick"):
                    self.end_tick = max(generator.loaded_messages, key=lambda x: x["tick"])["tick"]
                wrap_sum = self.end_tick // generator.wrap_length + 1
                note_shift = on_note["note"] - self.note_shift
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + note_shift} ~' \
                             f'{self.sum_y - generator.y_index} ' \
                             f'~{wrap_sum - generator.wrap_index + 1 + self.front_shift}' \
                             f' {{BlockState: {{Name: "{block_name}"}}, Time: 1, CustomName:' \
                             f'\'"{generator.tick_count}"\'}}'
            if generator._set_tick_command(x_shift=generator.build_index, y_shift=generator.y_index,
                                           z_shift=generator.wrap_index, command=summon_cmd):
                generator.y_index += 1
