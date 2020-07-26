from math import inf

from base.minecraft_types import *
from gsmidi.core import Generator
from gsmidi.plugins import Plugin


class PianoRoll(Plugin):
    __author__ = "kworker"
    __doc__ = """Shows a fancy piano roll"""

    DEFAULT_MAPPING = [
        "white", "orange", "magenta", "light_blue", "yellow",
        "lime", "pink", "gray", "light_gray", "cyan",
        "purple", "blue", "brown", "green", "red", "black",
    ]

    def __init__(self,
                 wrap_shift: "Moves the piano roll further away in wrap axis." = 1,
                 axis_y_shift: "Moves the piano roll further away in y axis." = 0,
                 reverse_wrap: "Move the piano roll to the last build row." = False,
                 mapping: "Maps the channels to the colors of the falling blocks." = None,
                 block_type: "'stained_glass', 'concrete', 'wool' or 'terracotta'" = None,
                 layered: "Show the piano roll in layers for different channels." = True):
        self.wrap_shift = wrap_shift
        self.axis_y_shift = axis_y_shift
        self.reverse_wrap = reverse_wrap
        self.mapping = mapping if mapping is not None else self.DEFAULT_MAPPING
        self.block_type = block_type if block_type in (
            'stained_glass', 'concrete', 'wool', 'terracotta'
        ) else "wool"
        self.layered = layered

    def init(self, generator: Generator):
        generator.wrap_length = inf  # Force no wrap

        function = Function(generator.namespace, "piano_roll")

        for on_note in generator.on_notes():  # Setblock for messages

            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'  # Get the name according to the mapping

            y_layer = self.layered * on_note["ch"]

            if self.reverse_wrap:
                wrap_shift = on_note["note"] - self.wrap_shift - 128  # Setblock to negative z
                function.extend([f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~-128",
                                 f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~-128"])
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.axis_y_shift + y_layer} ~{wrap_shift} minecraft:{block_name} replace"

            else:
                wrap_shift = on_note["note"] + self.wrap_shift  # # Setblock to positive z(default)
                function.extend([f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~128",
                                 f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~128"])
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.axis_y_shift + y_layer} ~{wrap_shift} minecraft:{block_name} replace"

            function.append(setblock_cmd)

        function.append(f"forceload remove all")
        generator.initial_functions.append(function)

        function = Function(generator.namespace, "pno_roll_effect")
        function.from_file("functions/pno_roll_effect.mcfunction")
        generator.extended_functions.append(function)

    def exec(self, generator: Generator):
        generator.set_tick_command(
            command=f"fill ~ ~{self.axis_y_shift - generator.y_index} ~1 ~ ~{self.axis_y_shift - generator.y_index} ~128 minecraft:air")

        toplevel_note = {}  # Reduces lag, improves performance

        for on_note in generator.current_on_notes()[::-1]:
            if on_note["note"] in toplevel_note.keys():  # Toplevel notes only
                continue

            z_shift = \
                on_note["note"] - self.wrap_shift - 128 if self.reverse_wrap else on_note["note"] + self.wrap_shift

            y_layer = self.layered * on_note["ch"]

            generator.set_tick_command(
                command=f"execute as @p positioned ~ ~{self.axis_y_shift - generator.y_index + y_layer} ~{z_shift} run function {generator.namespace}:pno_roll_effect")  # Execute the effect

            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'  # Get the name according to the mapping

            generator.set_tick_command(
                command=f'summon minecraft:falling_block ~ ~{self.axis_y_shift - generator.y_index + y_layer} ~{z_shift} {{BlockState:{{Name:"{block_name}"}},Time:1}}')  # Summon falling sand

            toplevel_note[on_note["note"]] = True
