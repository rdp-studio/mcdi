import random
from abc import abstractmethod
from math import sqrt, asin, degrees

from base.minecraft_types import *
from mid.core import BaseCbGenerator, float_range
from mid.frontends import vector_build
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
        generator.wrap_length = float("inf")  # Force no wrap

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
            function.from_file(f"funcs/piano_roll_blast_effect{i}.mcfunction")
            generator.runtime_functions.append(function)

    def exec(self, generator: BaseCbGenerator):
        for on_note in (on_notes := generator.current_on_notes()[::-1]):
            if len(on_notes) > self.effect_limit:
                break  # Too much notes, no effect.

            if self.parent.reverse_wrap:
                z_shift = on_note["note"] - self.parent.wrap_shift - 128
            else:
                z_shift = on_note["note"] + self.parent.wrap_shift

            y_layer = self.parent.layered * on_note["ch"]

            generator.add_tick_command(
                command=f"execute as @p positioned ~ ~{self.parent.axis_y_shift - generator.y_axis_index + y_layer} ~{z_shift} run function {generator.namespace}:pno_roll_effect{on_note['ch']}")  # Execute the effect

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
        on_notes = generator.current_on_notes()

        if self.effect_limit < len(on_notes):
            return None  # Too much notes, no effect.

        for ch in self.expr_mapping["channels"].keys():
            on_notes = generator.current_on_notes(ch=ch)
            if not on_notes: continue  # No note, no effect.

            tick = generator.tick_index + 1  # From the next tick...
            while not (futures := generator.future_on_notes(tick=tick, ch=ch)):
                tick += 1  # Find for the next tick.
                if tick >= generator.loaded_tick_count:
                    break  # Nothing more to be found.

            for future in futures:
                if not on_notes: break  # No note, no effect.
                nearest = self._find_nearest(future, on_notes)
                self._render_note(nearest, future, generator)

    def _render_note(self, on_note, future, generator: BaseCbGenerator):
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

        for function in self.expr_mapping["channels"][on_note["ch"]]["funcs"]:
            self._render_func(function, rel_dy, cx, cz, nx, nz, generator, on_note)

    def _render_func(self, function, rel_dy, cx, cz, nx, nz, generator: BaseCbGenerator, n):
        instance = function["instance"]
        particle = function["particle"] if "particle" in function else "minecraft:end_rod"
        arguments = function["arguments"] if "arguments" in function else {}
        composite = function["composite"] if "composite" in function else []
        visible = function["visible"] if "visible" in function else True
        dot_dist = function["dot_dist"] if "dot_dist" in function else self.dot_distance
        for x, y, z, delta_time, args in instance((cx, cz), (nx, nz), dot_dist, generator, n):
            args = dict(*args, *arguments)
            dx = args["dx"] if "dx" in args else 0
            dy = args["dy"] if "dy" in args else 0
            dz = args["dz"] if "dz" in args else 0
            s = args["speed"] if "speed" in args else 0
            c = args["count"] if "count" in args else 1
            rx, ry, rz = -delta_time, rel_dy, cz
            if visible:  # Not a base function
                generator.schedule(
                    delta_time, f"particle {particle} ~{x:.6f} ~{y:.6f} ~{z:.6f} {dx} {dy} {dz} {s} {c} force",
                    x=lambda s, _rx=rx: _rx, y=lambda s, _ry=ry: _ry - s.y_axis_index, z=lambda s, _rz=rz: _rz,
                )

    @staticmethod
    def _find_nearest(future, on_notes):
        min_dist = 2147438647
        min_note = on_notes[0]
        for on_note in on_notes:
            dz = future["note"] - on_note["note"]
            dx = future["tick"] - on_note["tick"]
            dist = (dx ** 2 + dz ** 2) ** .5
            if dist < min_dist: min_note, min_dist = on_note, dist  # Nearer than the last one
        return min_note

    def dependency_connect(self, dependencies):
        self.parent = next(dependencies)


class FunctionPreset(object):
    @abstractmethod
    def __call__(self, c, n, dd: float, generator: BaseCbGenerator, _) -> Tuple[float, float, float, int, dict]:
        pass


class LineFunctionPreset(FunctionPreset):  # Linear style gen.
    def __call__(self, c, n, dd: float, generator: BaseCbGenerator, _) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        dx = fx - cx
        dz = fz - cz
        r = dz / dx

        for i, x in enumerate(float_range(0, dx, dd)):
            yield x, 0, x * r, round(x), {}


class PowerFunctionPreset(FunctionPreset):  # Linear style gen.
    def __init__(self, height=.2, mirrored=False):
        self.k = height
        self.mirrored = mirrored

    def __call__(self, c, n, dd: float, generator: BaseCbGenerator, _) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        dx = fx - cx
        dz = fz - cz
        h = (self.k * dx ** 2) / 4

        def y_by_x(x):
            return -self.k * x ** 2 + h

        for i, x in enumerate(float_range(0, dx, dd)):
            y = y_by_x(x - dx / 2)
            z = dz * i / (dx / dd)
            if self.mirrored:
                y *= -1
            yield x, y, z, round(x), {}


class HelixFunctionPreset(FunctionPreset):  # Linear style gen.
    def __init__(self, r_init=0, r_delta=1.3, angle_f=90, phase=0):
        self.ir = r_init
        self.dr = r_delta
        self.af = angle_f
        self.phase = phase

    def __call__(self, c, n, dd: float, generator: BaseCbGenerator, _) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        dx = fx - cx
        dz = fz - cz

        for i, x in enumerate(float_range(0, dx, dd)):
            p = i / (dx / dd)  # Progress
            rf = 2 * (1 - p if p > .5 else p)
            rr = rf * self.dr + self.ir
            k = vector_build(
                self.af * x + self.phase, rr
            )
            z, y = k[0] + dz * p, k[1]
            yield x, y, z, round(x), {}


class OrbitFunctionPreset(FunctionPreset):  # Phase style gen.
    def __init__(self, r_rng=.5):
        self.r_rng = r_rng
        self.memory = [{
            "cw": False
        } for _ in range(16)]

    def __call__(self, c, n, dd: float, generator: BaseCbGenerator, _) -> Tuple[float, float, float, int, dict]:
        cx, cz, fx, fz = c + n
        dx = fx - cx
        dz = fz - cz

        r_min = (dx ** 2 + dz ** 2) ** .5  # Minimal distance
        rr = r_min * (1 + random.random() * self.r_rng)
        ox1, oz1, ox2, oz2 = self.centre_build(cx, cz, fx, fz, rr)
        ox, oz = random.choice([(ox1, oz1), (ox2, oz2)])  # Random centre
        dox, doz = ox + rr - cx, oz - cz
        dist1 = sqrt(dox ** 2 + doz ** 2)
        dox, doz = ox + rr - fx, oz - fz
        dist2 = sqrt(dox ** 2 + doz ** 2)
        co = degrees(asin(dist1 / 2 / rr)) * 2
        if cz < oz:
            co = 360 - co  # Current O
        fo = degrees(asin(dist2 / 2 / rr)) * 2
        if fz < oz:
            fo = 360 - fo  # Future O

        cw = self.memory[_["ch"]]["cw"]  # Memory
        ccw = self.memory[_["ch"]]["cw"] = not cw

        s = degrees(asin(r_min / 2 / rr)) * 2
        if fo > co and ccw:
            s = 360 - s
        if fo < co and cw:
            s = 360 - s

        if ccw:
            f = float_range(co, co - s, -dd)
        else:  # CW
            f = float_range(co, co + s, dd)

        base = None
        for i, a in enumerate(f):
            p = i / (s / dd)  # Progress
            z, x = vector_build(a, rr)
            if base is None:
                base = -x, -z
                yield 0, 0, 0, round(p * dx), {}
            else:
                x += base[0]
                z += base[1]
                yield x, 0, z, round(p * dx), {}

    @staticmethod
    def centre_build(x1, y1, x2, y2, r):
        o1 = (pow(x2, 2) - pow(x1, 2) + pow(y2, 2) - pow(y1, 2)) / 2 / (x2 - x1)
        o2 = (y2 - y1) / (x2 - x1)
        a = 1.0 + pow(o2, 2)
        b = 2 * (x1 - o1) * o2 - 2 * y1
        c = pow((x1 - o1), 2) + pow(y1, 2) - pow(r, 2)
        oy1 = (-b + sqrt(b * b - 4 * a * c)) / 2 / a
        ox1 = o1 - o2 * oy1
        oy2 = (-b - sqrt(b * b - 4 * a * c)) / 2 / a
        ox2 = o1 - o2 * oy2
        return ox1, oy1, ox2, oy2
