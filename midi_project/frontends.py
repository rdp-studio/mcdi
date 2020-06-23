import logging
from math import floor


class Frontend(object):
    def __init__(self):
        pass

    def get_play_cmd(self, **kwargs):
        pass

    def get_stop_cmd(self, **kwargs):
        pass


class Soma(Frontend):
    """The fundamental frontend for project MCDI."""

    soma_long_safe = (  # These are the long notes.
        1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        38, 39, 40, 41, 42, 43, 44, 45, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 120)

    def __init__(self):
        super().__init__()

    @classmethod
    def get_play_cmd(cls, prog, note, v, pan, pitch, long, half, **kwargs):
        abs_pan = (pan - 64) / 32
        prog = str(prog) + "c" * (prog in cls.soma_long_safe and long)
        note = str(note) + "d" * bool(half)
        return f"execute as @a at @s run playsound {prog}.{note} voice @s " \
               f"^{-abs_pan} ^ ^{2 - abs(abs_pan)} {v / 255} {pitch}"

    @classmethod
    def get_stop_cmd(cls, prog, note, long, half, **kwargs):
        prog = str(prog) + "c" * (prog in cls.soma_long_safe and long)
        note = str(note) + "d" * bool(half)
        return f"execute as @a at @s run stopsound @s voice {prog}.{note}"


class Vanilla(Frontend):
    """The vanilla minecraft frontend, smaller sound range. (By HydrogenC)"""

    pitches = [0.5, 0.529732, 0.561231, 0.594604, 0.629961, 0.667420, 0.707107, 0.749154, 0.793701, 0.840896, 0.890899,
               0.943874, 1, 1.059463, 1.122462, 1.189207, 1.259921, 1.334840, 1.414214, 1.498307, 1.587401, 1.681793,
               1.781797, 1.887749, 2]

    insts_pitch = {"bass": 1, "bell": 5, "flute": 4, "chime": 5, "guitar": 2, "xylophone": 5, "iron_xylophone": 3,
                   "cow_bell": 4, "didgeridoo": 1, "bit": 3, "banjo": 3, "pling": 3, "harp": 3}

    def __init__(self, f1_inst: "Instrument to play F#1-F#2 with" = "bass",
                 f2_inst: "Instrument to play F#2-F#3 with" = "bass",
                 f3_inst: "Instrument to play F#3-F#4 with" = "harp",
                 f4_inst: "Instrument to play F#4-F#5 with" = "harp",
                 f5_inst: "Instrument to play F#5-F#6 with" = "bell",
                 f6_inst: "Instrument to play F#6-F#7 with" = "bell",
                 use_stop: "Use the stopsound command" = False):
        super().__init__()
        self.insts = f1_inst, f2_inst, f3_inst, f4_inst, f5_inst, f6_inst
        self.use_stop = use_stop

        for i, inst in enumerate(self.insts):
            if not self.insts.__contains__(inst):
                raise ValueError(f"Invalid instrument name: {inst}")
            if self.insts_pitch[inst] > (i + 1) or (self.insts_pitch[inst] + 2) < (i + 1):
                raise ValueError(f"Instrument does not cover the specified range: {inst}")

    def get_play_cmd(self, prog, note, v, pan, pitch, long, half, **kwargs):
        if note < 18 or note > 90:
            logging.info(f"On note {note} at channel{prog} out of range! ")
            return f'tellraw @a {{"text":"[ERROR] Invalid pitch from note {note} at channel{prog}","color":"red"}}'

        abs_pan = (pan - 64) / 32
        inst_num = floor(((note - 18) / 12) if note != 90 else 5)
        start_pitch = self.insts_pitch[(inst := self.insts[inst_num])]
        return f"execute as @a at @s run playsound minecraft:block.note_block.{inst} voice @s ^{-abs_pan} ^ ^{2 - abs(abs_pan)} {v / 255} {self.pitches[note - start_pitch * 18]}"

    def get_stop_cmd(self, prog, note, long, half, **kwargs):
        if not self.use_stop:
            return None

        if note < 18 or note > 90:
            logging.info(f"Off note {note} at{prog} channel out of range! ")
            return None

        inst_num = floor(((note - 18) / 12) if note != 90 else 5)
        inst = self.insts[inst_num]
        return f"execute as @a at @s run stopsound @s voice minecraft:block.note_block.{inst}"

class Mcrg(Frontend):
    """The frontend to generate music for mcrg resource packs. (By HydrogenC)"""

    def __init__(self, packname:"Name of the target resource pack"="mcrg",
                 use_stop: "Use the stopsound command" = False):
        self.packname=packname;
        self.use_stop=use_stop;

    def get_play_cmd(self, prog, note, v, pan, pitch, long, half, **kwargs):
        abs_pan = (pan - 64) / 32
        return f"execute as @a at @s run stopsound @s voice {self.packname}.{pitch}"

    def get_stop_cmd(self, prog, note, long, half, **kwargs):
        if not self.use_stop:
            return None
        return f"execute as @a at @s run stopsound {self.packname}.{pitch} voice @s"
