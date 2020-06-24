from midi_project.core import Generator
from command_types import *


class Plugin(object):
    def exec(self, generator: Generator):
        pass

    def init(self, generator: Generator):
        pass


class Progress(Plugin):
    __author__ = "kworker"
    __doc__ = """Simply shows a progress bar"""

    def __init__(self, pk: "The ID for the bossbar, no need to care for in most cases." = 0,
                 text: "The title for the bossbar to show on the top." = "MCDI",
                 color: "The color for the bossbar and the title." = "yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator: Generator):
        if not hasattr(self, "end_tick"):
            self.end_tick = max(generator.loaded_messages, key=lambda x: x["tick"])["tick"]
        if generator.tick_index == 0:
            cmd = f'bossbar add {self.pk} {{"text": "{self.text}"}}'
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} color {self.color}"
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} max {self.end_tick}"
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} players @a"
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            cmd = f"bossbar set {self.pk} visible true"
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            return None
        if generator.tick_index == self.end_tick:
            cmd = f"bossbar set {self.pk} visible false"
            if generator._set_tick_command(command=cmd):
                generator.y_index += 1
            return None
        if generator._set_tick_command(command=f"bossbar set {self.pk} value {generator.tick_index}"):
            generator.y_index += 1


class PianoFall(Plugin):
    __author__ = "kworker"
    __doc__ = """Shows a fancy piano fall"""

    def __init__(self, front_tick: "How many ticks before should the command blocks summon falling blocks." = 90,
                 summon_height: "How high should the command blocks summon falling blocks." = 100,
                 build_shift: "Moves the piano fall further away in build axis." = 0,
                 wrap_shift: "Moves the piano fall further away in wrap axis." = 1,
                 reversed: "Move the piano fall from the first to the last build row." = False,
                 mapping: "Maps the channels to the colors of the falling blocks." = None,
                 block_type: "'stained_glass', 'concrete', 'wool' or 'terracotta'" = None):
        self.front_tick = front_tick
        self.sum_y = summon_height
        self.build_shift = build_shift
        self.wrap_shift = wrap_shift
        self.reversed = reversed
        self.mapping = mapping if mapping is not None else [
            "white", "orange", "magenta", "light_blue", "yellow",
            "lime", "pink", "gray", "light_gray", "cyan",
            "purple", "blue", "brown", "green", "red", "black",
        ]
        self.block_type = block_type if block_type in ('stained_glass', 'concrete', 'wool', 'terracotta') else "wool"

    def init(self, generator: Generator):
        generator.blank_ticks += self.front_tick

    def exec(self, generator: Generator):
        on_notes = list()
        expected_tick = generator.tick_index + self.front_tick
        for message in generator.loaded_messages:
            if message["type"] != "note_on":
                continue
            if message["tick"] < expected_tick:
                continue
            if message["tick"] == expected_tick:
                on_notes.append(message)
            if message["tick"] > expected_tick:
                break

        for on_note in on_notes:
            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'
            if self.reversed:
                build_shift = self.build_shift - on_note["note"] + 128
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + build_shift} ~{self.sum_y - generator.y_index} ~{-generator.wrap_index - 1 - self.wrap_shift} {{BlockState:{{Name: "{block_name}"}},Time:1,CustomName:\'"{generator.tick_index}"\'}}'
            else:
                wrap_sum = generator.tick_sum // generator.wrap_length + 1
                build_shift = on_note["note"] - self.build_shift
                summon_cmd = f'summon minecraft:falling_block ~{-generator.build_index + build_shift} ~{self.sum_y - generator.y_index} ~{wrap_sum - generator.wrap_index + 1 + self.wrap_shift}{{BlockState:{{Name:"{block_name}"}},Time:1,CustomName:\'"{generator.tick_index}"\'}}'
            if generator._set_tick_command(command=summon_cmd):
                generator.y_index += 1

        if generator._set_tick_command(command=f"kill @e[name={generator.tick_index - self.front_tick}]"):
            generator.y_index += 1


class PianoRoll(Plugin):
    __author__ = "kworker"
    __doc__ = """Shows a fancy piano roll"""

    def __init__(self, wrap_shift: "Moves the piano fall further away in wrap axis." = 1,
                 y_shift: "Moves the piano fall further away in y axis." = 0,
                 reversed: "Move the piano fall from the first to the last build row." = False,
                 mapping: "Maps the channels to the colors of the falling blocks." = None,
                 block_type: "'stained_glass', 'concrete', 'wool' or 'terracotta'" = None,
                 jump2_min: "The minimum distance of the next note to jump2 to." = 1,
                 jump2_max: "The maximum distance of the next note to jump2 to." = 100):
        self.wrap_shift = wrap_shift
        self.y_shift = y_shift
        self.reversed = reversed
        self.mapping = mapping if mapping is not None else [
            "white", "orange", "magenta", "light_blue", "yellow",
            "lime", "pink", "gray", "light_gray", "cyan",
            "purple", "blue", "brown", "green", "red", "black",
        ]
        self.block_type = block_type if block_type in ('stained_glass', 'concrete', 'wool', 'terracotta') else "wool"
        self.jump2_min, self.jump2_max = jump2_min, jump2_max

    def init(self, generator: Generator):
        generator.wrap_length = float("inf")
        function = Function(generator.namespace, "pno_roll")
        for on_note in generator.loaded_messages:
            if on_note["type"] != "note_on":
                continue
            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'
            if self.reversed:
                wrap_shift = on_note["note"] - self.wrap_shift - 128
                function.append(f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~-128")
                function.append(f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~-128")
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.y_shift} ~{wrap_shift} minecraft:{block_name} replace"
            else:
                wrap_shift = on_note["note"] + self.wrap_shift
                function.append(f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~128")
                function.append(f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~128")
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.y_shift} ~{wrap_shift} minecraft:{block_name} replace"
            function.append(setblock_cmd)
        function.append(f"forceload remove all")
        generator.initial_functions.append(function)

        function = Function(generator.namespace, "pno_roll_effect1")
        function.read("midi_project/functions/pno_roll_effect1.mcfunction")
        generator.extended_functions.append(function)

    def exec(self, generator: Generator):
        clear_cmd = f"fill ~ ~{self.y_shift - generator.y_index} ~1 ~ ~{self.y_shift - generator.y_index} ~128 minecraft:air"
        if generator._set_tick_command(command=clear_cmd):
            generator.y_index += 1
        execute_cmd = f"execute as @a at @s run tp @s ~1 ~ ~"
        if generator._set_tick_command(command=execute_cmd):
            generator.y_index += 1

        on_notes = list()
        for message in generator.tick_cache:
            if message["type"] != "note_on":
                continue
            on_notes.append(message)

        for on_note in on_notes:
            if self.reversed:
                wrap_shift = on_note["note"] - self.wrap_shift - 128
            else:
                wrap_shift = on_note["note"] + self.wrap_shift
            execute_cmd = f"execute positioned ~ ~{self.y_shift - generator.y_index} ~{wrap_shift} run function {generator.namespace}:pno_roll_effect1"
            if generator._set_tick_command(command=execute_cmd):
                generator.y_index += 1

            jump2_notes = list()
            found_tick = -1
            for message in generator.loaded_messages:
                if message["type"] != "note_on":
                    continue
                if message["ch"] != on_note["ch"]:
                    continue
                if message["tick"] != found_tick and found_tick > 0:
                    break
                jump2_notes.append(message)
                found_tick = message["tick"]
            jump2_notes = filter(
                lambda x: self.jump2_min < x["tick"] - on_note["tick"] < self.jump2_max, jump2_notes
            )

            for jump2_note in jump2_notes:
                dx = t = jump2_note["tick"] - on_note["tick"]
                if self.reversed:
                    dz = (jump2_note["note"] - self.wrap_shift - 128) - wrap_shift
                else:
                    dz = (jump2_note["note"] + self.wrap_shift) - wrap_shift
                block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'
                velocity = map(lambda x: str(x), self.get_jump_velocity(dx, 0, dz, t))
                summon_cmd = f'summon minecraft:falling_block ~ ~{self.y_shift - generator.y_index} ~{wrap_shift} {{BlockState:{{Name:"{block_name}"}},Time:1,Motion:[{",".join(velocity)}]}}'
                if generator._set_tick_command(command=summon_cmd):
                    generator.y_index += 1

    @staticmethod
    def get_jump_velocity(dx, dy, dz, t):
        x = 0.02 * dx / (1 - 0.98 ** t)
        y = (0.02 * dy + 0.04 * (t - 1)) / (1 - 0.98 ** (t - 1)) - 1.96
        z = 0.02 * dz / (1 - 0.98 ** t)
        return x, y, z
