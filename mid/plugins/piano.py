from math import inf

from base.minecraft_types import *
from mid.core import BaseCbGenerator, float_range
from mid.plugins import Plugin


class PianoRoll(Plugin):
    __author__ = "kworker"
    __doc__ = """Shows a fancy piano roll."""

    def __init__(self,
                 wrap_shift: "Moves the piano roll further away in wrap axis." = 1,
                 axis_y_shift: "Moves the piano roll further away in y axis." = 0,
                 reverse_wrap: "Move the piano roll to the last build row." = False,
                 mapping: "Maps the channels to the colors of the falling blocks." = None,
                 block_type: "'stained_glass', 'concrete', 'wool' or 'terracotta'" = None,
                 layered: "Show the piano roll in layers for different channels." = True,
                 ):
        self.wrap_shift = wrap_shift
        self.axis_y_shift = axis_y_shift
        self.reverse_wrap = reverse_wrap

        self.mapping = mapping if mapping is not None else (
            "black", "blue", "brown", "cyan", "gray", "green", "light_blue", "light_gray",
            "lime", "magenta", "orange", "pink", "purple", "red", "white", "yellow"
        )

        self.block_type = block_type if block_type in (
            'stained_glass', 'concrete', 'wool', 'terracotta'
        ) else "wool"

        self.layered = layered

    def init(self, generator: BaseCbGenerator):
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


class PianoRollFirework(Plugin):
    __author__ = "kworker"
    __doc__ = "Fireworks of notes for 'PianoRoll'."

    __dependencies__ = [PianoRoll]

    def __init__(self,
                 effect_limit: "Show effects only when note number lt this value." = 65535):
        self.parent: PianoRoll
        self.effect_limit = effect_limit

    def init(self, generator: BaseCbGenerator):
        for i in range(16):
            function = Function(generator.namespace, f"pno_roll_effect{i}")
            function.from_file(f"functions/piano_roll_blast_effect{i}.mcfunction")
            generator.extended_functions.append(function)

    def exec(self, generator: BaseCbGenerator):
        toplevel_note = {}  # Reduces lag, improves performance

        for on_note in (on_notes := generator.current_on_notes()[::-1]):
            if on_note["note"] in toplevel_note.keys():
                continue  # When not layered, toplevel notes only

            if len(on_notes) > self.effect_limit:
                continue  # Too much notes, no effect.

            if self.parent.reverse_wrap:
                z_shift = on_note["note"] - self.parent.wrap_shift - 128
            else:
                z_shift = on_note["note"] + self.parent.wrap_shift

            y_layer = self.parent.layered * on_note["ch"]

            generator.add_tick_command(
                command=f"execute as @p positioned ~ ~{self.parent.axis_y_shift - generator.y_axis_index + y_layer} ~{z_shift} run function {generator.namespace}:pno_roll_effect{on_note['ch']}")  # Execute the effect

            if not self.parent.layered:
                toplevel_note[on_note["note"]] = True

    def dependency_connect(self, dependencies):
        self.parent = next(dependencies)
