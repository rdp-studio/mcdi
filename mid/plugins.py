import re
from math import inf

from base.minecraft_types import *
from mid.core import Generator


class Plugin(object):
    def exec(self, generator: Generator):
        pass

    def init(self, generator: Generator):
        pass


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
                 block_type: "'stained_glass', 'concrete', 'wool' or 'terracotta'" = None):
        self.wrap_shift = wrap_shift
        self.axis_y_shift = axis_y_shift
        self.reverse_wrap = reverse_wrap
        self.mapping = mapping if mapping is not None else self.DEFAULT_MAPPING
        self.block_type = block_type if block_type in (
            'stained_glass', 'concrete', 'wool', 'terracotta'
        ) else "wool"
        self.future_messages = []

    def init(self, generator: Generator):
        self.future_messages = generator.loaded_messages.copy()

        generator.wrap_length = inf  # Force no wrap
        function = Function(generator.namespace, "piano_roll")

        for on_note in generator.on_notes():  # Setblock for messages

            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'  # Get the name according to the mapping

            if self.reverse_wrap:
                wrap_shift = on_note["note"] - self.wrap_shift - 128  # Setblock to negative z
                function.extend([f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~-128",
                                 f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~-128"])
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.axis_y_shift} ~{wrap_shift} minecraft:{block_name} replace"

            else:
                wrap_shift = on_note["note"] + self.wrap_shift  # # Setblock to positive z(default)
                function.extend([f"forceload remove ~{on_note['tick'] - 1} ~ ~{on_note['tick'] - 1} ~128",
                                 f"forceload add ~{on_note['tick']} ~ ~{on_note['tick']} ~128"])
                setblock_cmd = f"setblock ~{on_note['tick']} ~{self.axis_y_shift} ~{wrap_shift} minecraft:{block_name} replace"

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

            generator.set_tick_command(
                command=f"execute as @s positioned ~ ~{self.axis_y_shift - generator.y_index} ~{z_shift} run function {generator.namespace}:pno_roll_effect")  # Execute the effect

            block_name = f'{self.mapping[on_note["ch"] - 1]}_{self.block_type}'  # Get the name according to the mapping

            generator.set_tick_command(
                command=f'summon minecraft:falling_block ~ ~{self.axis_y_shift - generator.y_index} ~{z_shift} {{BlockState:{{Name:"{block_name}"}},Time:1}}')  # Summon falling sand

            toplevel_note[on_note["note"]] = True


class Viewport(Plugin):
    __author__ = "kworker"
    __doc__ = """Fixed or flexible viewport, useful for video making"""

    def __init__(self,
                 x: "The initial relative x-axis of the viewport." = -16,
                 y: "The initial relative y-axis of the viewport." = 32,
                 z: "The initial relative z-axis of the viewport." = 64,
                 fx: "The initial relative facing in x-axis of the viewport." = 0,
                 fy: "The initial relative facing in y-axis of the viewport." = 16,
                 fz: "The initial relative facing in z-axis of the viewport." = 64,
                 fixed: "Fix the player to the position during the music." = True):
        self.position = x, y, z
        self.facing = fx, fy, fz
        self.fixed = fixed

    def exec(self, generator: Generator):
        if self.fixed or generator.is_first_tick:  # Fixed viewport
            x, y, z = self.position
            fx, fy, fz = self.facing
            y -= generator.y_index
            fy -= generator.y_index
            generator.set_tick_command(command=f"tp @a ~{x} ~{y} ~{z} facing ~{fx} ~{fy} ~{fz}")
        else:  # Just move forward
            generator.set_tick_command(command=f"execute as @a at @s run tp @s ~1 ~ ~")


class Titler(Plugin):
    __author__ = "kworker"
    __doc__ = """Title at the beginning and the end, useful for video making"""

    DEFAULT_IN_TITLE = {
        "text": "Codename: MCDI",
        "color": "green"
    }
    DEFAULT_IN_SUBTITLE = {
        "text": "By kworker (Frank Yang)"
    }
    DEFAULT_OUT_TITLE = {
        "text": "谢谢你看完这个视频!",
        "color": "red"
    }
    DEFAULT_OUT_SUBTITLE = {
        "text": "喜欢就给我个三连吧~"
    }

    def __init__(self,
                 in_title: "The big title when the music starts." = None,
                 in_subtitle: "The small title when the music starts." = None,
                 out_title: "The big title when the music ends." = None,
                 out_subtitle: "The small title when the music ends." = None):
        self.in_title = in_title if in_title is not None else self.DEFAULT_IN_TITLE
        self.in_subtitle = in_subtitle if in_subtitle is not None else self.DEFAULT_IN_SUBTITLE
        self.out_title = out_title if out_title is not None else self.DEFAULT_OUT_TITLE
        self.out_subtitle = out_subtitle if out_subtitle is not None else self.DEFAULT_OUT_SUBTITLE

    def exec(self, generator: Generator):
        if generator.is_first_tick:  # At the beginning
            generator.set_tick_command(command=f"title @a title {json.dumps(self.in_title, ensure_ascii=False)}")
            generator.set_tick_command(command=f"title @a subtitle {json.dumps(self.in_subtitle, ensure_ascii=False)}")
        elif generator.is_last_tick:  # At the end
            generator.set_tick_command(command=f"title @a title {json.dumps(self.out_title, ensure_ascii=False)}")
            generator.set_tick_command(command=f"title @a subtitle {json.dumps(self.out_subtitle, ensure_ascii=False)}")


class Lyric(Plugin):
    __author__ = "kworker"
    __doc__ = """Lyric throughout the music, useful for video making"""

    def __init__(self, fp):
        self.lyric_ticks = {}

        with open(fp, "r", encoding="utf8") as lyric:  # Open lyric file
            lyric_lines = lyric.readlines()

        for line_number, lyric_line in enumerate(lyric_lines):
            if match := re.findall(r"\[(\d\d):(\d\d)\.(\d\d)]\s*(.+)\n?", lyric_line):
                m, s, ms, lyric = match[0]  # Unpack tuple
            elif match := re.findall(r"\[(ti|ar|al|by|offset):.+?\].*?\n?", lyric_line):
                continue  # Ignore these meta messages
            elif not lyric_line.strip():
                continue  # Ignore these blank lines
            else:
                raise SyntaxError(f"Malformed LRC syntax in line {line_number}.")

            self.lyric_ticks[round((int(m) * 60 + int(s) + int(ms) / 100) * 20)] = lyric

    def exec(self, generator: Generator):
        if generator.tick_index in self.lyric_ticks.keys():  # Add a line of lyric, shows in actionbar
            generator.set_tick_command(command=f'title @a actionbar "{self.lyric_ticks[generator.tick_index]}"')

class Progress(Plugin):
    __author__ = "kworker"
    __doc__ = """Simply shows a progress bar, useful for video making"""

    def __init__(self,
                 pk: "The ID for the bossbar. For professional users only." = 0,
                 text: "The title for the bossbar to show on the top." = "MCDI",
                 color: "The color for the bossbar and the title." = "yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator: Generator):
        if generator.is_first_tick:
            generator.set_tick_command(f'bossbar add {self.pk} {{"text": "{self.text}"}}')
            generator.set_tick_command(command=f"bossbar set {self.pk} color {self.color}")
            generator.set_tick_command(command=f"bossbar set {self.pk} max {generator.loaded_tick_count}")
            generator.set_tick_command(command=f"bossbar set {self.pk} players @a")
            generator.set_tick_command(command=f"bossbar set {self.pk} visible true")
            return None
        if generator.is_last_tick:
            generator.set_tick_command(command=f"bossbar set {self.pk} visible false")
            return None
        generator.set_tick_command(command=f"bossbar set {self.pk} value {generator.tick_index}")
