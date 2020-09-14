from math import inf, sqrt

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
                 real_len: "Show the real length of the note. Note links required." = False,
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
        self.real_len = real_len

    def init(self, generator: BaseCbGenerator):
        generator.wrap_length = inf  # Force no wrap

        function = Function(generator.namespace, "piano_roll")

        for on_note in generator.on_notes():  # Setblock for messages

            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'  # Get the name according to the mapping

            y_layer = self.layered * on_note["ch"]

            if on_note["linked"] is not None and self.real_len:
                duration = on_note["linked"][0] - on_note["linked"][1]
            else:
                duration = 0

            if self.reverse_wrap:
                wrap_shift = on_note["note"] - self.wrap_shift - 128  # Setblock to negative z
                function.extend(
                    [f"forceload remove all", f"forceload add ~{on_note['tick']} ~ ~{on_note['tick'] + duration} ~-128"]
                )
                setblock_cmd = f"fill ~{on_note['tick']} ~{self.axis_y_shift + y_layer} ~{wrap_shift} ~{on_note['tick'] + duration} ~{self.axis_y_shift + y_layer} ~{wrap_shift} minecraft:{block_name} replace"

            else:
                wrap_shift = on_note["note"] + self.wrap_shift  # # Setblock to positive z(default)
                function.extend(
                    [f"forceload remove all", f"forceload add ~{on_note['tick']} ~ ~{on_note['tick'] + duration} ~128"]
                )
                setblock_cmd = f"fill ~{on_note['tick']} ~{self.axis_y_shift + y_layer} ~{wrap_shift} ~{on_note['tick'] + duration} ~{self.axis_y_shift + y_layer} ~{wrap_shift} minecraft:{block_name} replace"

            function.append(setblock_cmd)

        function.append(f"forceload remove all")
        generator.gentime_functions.append(function)


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
            generator.runtime_functions.append(function)

    def exec(self, generator: BaseCbGenerator):
        toplevel_note = {}  # Reduces lag, improves performance

        for on_note in (on_notes := generator.current_on_notes()[::-1]):
            if on_note["note"] in toplevel_note.keys():
                continue  # When not layered, toplevel notes only

            if len(on_notes) > self.effect_limit:
                break  # Too much notes, no effect.

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


class PianoRollRenderer(Plugin):
    __author__ = "kworker"
    __doc__ = "3D effects of notes for 'PianoRoll'."

    __dependencies__ = [PianoRoll]

    def __init__(self,
                 expressions: "The pattern expressions(in lambda) for channels." = None,
                 dot_distance: "The distance between two particles in the patterns." = .3,
                 effect_limit: "Show effects only when note number lt this value." = 65535):
        """
        Expression Syntax:
        {
            "functions": [
                Callable[
                    Tuple[float, float, float],
                    Tuple[float, float, float],
                    float, BaseCbGenerator
                ] -> Tuple[float, float, float, int, dict],
                ...
            ],
            "channels": Union[list, "*"],
            "tracks": Union[list, "*"],
            "particle": Union[str, None],
            "additional": {
                "dx": ...,
                "dy": ...,
                "dz": ...,
                "speed": ...,
                ...
            }
        }
        """

        self.parent: PianoRoll
        if expressions is None:
            self.expressions = []
        else:
            self.expressions = list(expressions)
        self.expr_mapping = {
            "tracks": {},
            "channels": {}
        }
        self.dot_distance = dot_distance
        self.effect_limit = effect_limit

    def init(self, generator: BaseCbGenerator):
        track_count = len(generator.tracks)

        for expr in self.expressions:
            if expr["channels"] == "*":
                channels = range(0, 16)
            else:
                channels = expr["channels"]
            for i in channels:
                self.expr_mapping["channels"][i] = expr

            if expr["tracks"] == "*":
                tracks = range(0, track_count)
            else:
                tracks = expr["tracks"]
            for i in tracks:
                self.expr_mapping["tracks"][i] = expr

    def exec(self, generator: BaseCbGenerator):
        toplevel_note = {}  # Reduces lag, improves performance
        rendered_notes = []

        for on_note in (on_notes := generator.current_on_notes()[::-1]):
            if on_note["note"] in toplevel_note.keys():
                continue  # When not layered, toplevel notes only

            if len(on_notes) > self.effect_limit:
                break  # Too much notes, no effect.

            if on_note["ch"] not in self.expr_mapping["channels"].keys():
                continue  # No way!

            if on_note is on_notes[-1]:
                for future in generator.future_on_notes(ch=on_note["ch"]):
                    if future in rendered_notes:
                        continue
                    self._render(on_note, future, generator)
                    rendered_notes.append(future)
            else:
                min_distance, nearest_future = float(inf), None

                for future in generator.future_on_notes(ch=on_note["ch"]):
                    if future in rendered_notes:
                        continue
                    distance = abs(future["note"] - on_note["note"])
                    if distance < min_distance:
                        min_distance = distance
                        nearest_future = future

                if nearest_future is not None:
                    self._render(on_note, nearest_future, generator)
                    rendered_notes.append(nearest_future)

            if not self.parent.layered:
                toplevel_note[on_note["note"]] = True

    def _render(self, on_note, future, generator: BaseCbGenerator):
        if self.parent.reverse_wrap:
            z_shift = on_note["note"] - self.parent.wrap_shift - 128
        else:
            z_shift = on_note["note"] + self.parent.wrap_shift

        cx, cz = 0, z_shift

        if self.parent.reverse_wrap:
            z_shift = future["note"] - self.parent.wrap_shift - 128
        else:
            z_shift = future["note"] + self.parent.wrap_shift

        nx, nz = future["tick"] - on_note["tick"], z_shift
        y_layer = self.parent.layered * on_note["ch"]
        rel_dy = self.parent.axis_y_shift + y_layer

        for function in (expr := self.expr_mapping["channels"][on_note["ch"]])["functions"]:
            for x, y, z, delta_time, add in function((cx, cz), (nx, nz), self.dot_distance, generator):
                additional = dict(*add, *expr["additional"])
                dx = additional["dx"] if "dx" in additional else 0
                dy = additional["dy"] if "dy" in additional else 0
                dz = additional["dz"] if "dz" in additional else 0
                s = additional["speed"] if "speed" in additional else 0
                c = additional["count"] if "count" in additional else 1
                rx, ry, rz = -delta_time, rel_dy, cz
                generator.schedule(
                    delta_time, f"particle {expr['particle']} ~{x} ~{y} ~{z} {dx} {dy} {dz} {s} {c} force",
                    x=lambda s, _rx=rx: _rx, y=lambda s, _ry=ry: _ry - s.y_axis_index, z=lambda s, _rz=rz: _rz,
                )

    def dependency_connect(self, dependencies):
        self.parent = next(dependencies)


class LineFunctionPreset(object):
    def __call__(self, c, n, dd: float, generator: BaseCbGenerator) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        length = sqrt((fx - cx) ** 2 + (fz - cz) ** 2)
        dc = length / dd
        dx = fx - cx
        dz = fz - cz
        ratio = dz / dx

        for x in float_range(0, dx, dx / dc):
            z = x * ratio
            yield x, 0, z, round(x), {}


class PowerFunctionPreset(object):
    def __init__(self, k=.2):
        self.k = k

    def __call__(self, c, n, dd: float, generator: BaseCbGenerator) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        mw = fx - cx
        mh = (self.k * mw ** 2) / 4
        f = lambda x: -self.k * x ** 2 + mh

        for i, x in enumerate(float_range(0, mw, dd)):
            y = f(x - mw / 2)
            z = (fz - cz) * i / (mw / dd)
            yield x, y, z, round(x), {}
