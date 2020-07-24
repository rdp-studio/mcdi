import logging
from math import floor


class Frontend(object):
    def __init__(self):
        pass

    def get_play_cmd(self, **kwargs) -> str:
        pass

    def get_stop_cmd(self, **kwargs) -> str:
        pass


class Soma(Frontend):
    """The fundamental frontend for project MCDI."""

    LONG_SAFE = (  # These are the long notes.
        1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        38, 39, 40, 41, 42, 43, 44, 45, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 120
    )

    def __init__(self,
                 use_stop: "Use the stopsound command" = True):
        super().__init__()
        self.use_stop = use_stop

    def get_play_cmd(self, program, note, v, phase, pitch, long, half, **kwargs):
        abs_phase = (phase - 64) / 32  # Convent [0 <= int <= 127] to [-2 <= float <= 2].
        return f"execute as @a at @s run playsound {str(program) + 'c' * (program in self.LONG_SAFE and long)}.{str(note) + 'd' * bool(half)} voice @s ^{-abs_phase} ^ ^{2 - abs(abs_phase)} {v / 255} {pitch}"

    def get_stop_cmd(self, program, note, long, half, **kwargs):
        if not self.use_stop:
            return None

        return f"execute as @a at @s run stopsound @s voice {str(program) + 'c' * (program in self.LONG_SAFE and long)}.{str(note) + 'd' * bool(half)}"


class Vanilla(Frontend):
    """The vanilla minecraft frontend, smaller sound range. (By HydrogenC)"""

    pitches = (  # These are the pitches in two octaves
        0.5, 0.529732, 0.561231, 0.594604, 0.629961, 0.667420, 0.707107, 0.749154, 0.793701, 0.840896, 0.890899,
        0.943874, 1, 1.059463, 1.122462, 1.189207, 1.259921, 1.334840, 1.414214, 1.498307, 1.587401, 1.681793, 1.781797,
        1.887749, 2
    )

    insts_pitch = {
        "bass": 1,
        "bell": 5,
        "flute": 4,
        "chime": 5,
        "guitar": 2,
        "xylophone": 5,
        "iron_xylophone": 3,
        "cow_bell": 4,
        "didgeridoo": 1,
        "bit": 3,
        "banjo": 3,
        "pling": 3,
        "harp": 3
    }

    def __init__(self,
                 f1_inst: "Instrument to play F#1-F#2 with" = "bass",
                 f2_inst: "Instrument to play F#2-F#3 with" = "bass",
                 f3_inst: "Instrument to play F#3-F#4 with" = "harp",
                 f4_inst: "Instrument to play F#4-F#5 with" = "harp",
                 f5_inst: "Instrument to play F#5-F#6 with" = "bell",
                 f6_inst: "Instrument to play F#6-F#7 with" = "bell",
                 use_stop: "Use the stopsound command" = True):
        super().__init__()
        self.insts = f1_inst, f2_inst, f3_inst, f4_inst, f5_inst, f6_inst
        self.use_stop = use_stop

        for i, inst in enumerate(self.insts):
            if inst not in self.insts:
                raise ValueError(f"Instrument name not in {self.insts_pitch.keys()}: {inst}")
            if self.insts_pitch[inst] > (i + 1) or (self.insts_pitch[inst] + 2) < (i + 1):
                raise ValueError(f"Instrument does not cover the specified range: {inst}")

    def get_play_cmd(self, ch, note, v, phase, **kwargs):
        if note < 18 or note > 90:
            logging.warning(f"On note {note} at channel{ch} out of range! ")
            return None

        abs_phase = (phase - 64) / 32  # Convent [0 <= int <= 127] to [-2 <= float <= 2].
        inst_index = floor(((note - 18) / 12) if note != 90 else 5)  # Get the instrument to use(in range)
        base_pitch = self.insts_pitch[(inst := self.insts[inst_index])]  # Get the pitch for the instrument
        return f"execute as @a at @s run playsound minecraft:block.note_block.{inst} voice @s ^{-abs_phase} ^ ^{2 - abs(abs_phase)} {v / 255} {self.pitches[note - base_pitch * 18]}"

    def get_stop_cmd(self, ch, note, **kwargs):
        if not self.use_stop:
            return None

        if note < 18 or note > 90:
            logging.warning(f"Off note {note} at channel{ch} out of range! ")
            return None

        inst_index = floor(((note - 18) / 12) if note != 90 else 5)  # Get the instrument to use(in range)
        base_pitch = self.insts_pitch[(inst := self.insts[inst_index])]  # Get the pitch for the instrument
        return f"execute as @a at @s run stopsound minecraft:block.note_block.{self.insts[inst_index]} voice @s"


class Mcrg(Frontend):
    """The MCRG resourcepack frontend, like auto-tune remix. (By HydrogenC)"""

    def __init__(self,
                 pack_name: "Name of the target resourcepack" = "mcrg",
                 inst_name: "Name of the target instrument" = "inst",
                 use_stop: "Use the stopsound command" = True):
        super().__init__()
        self.pack_name = pack_name
        self.inst_name = inst_name
        self.use_stop = use_stop

    def get_play_cmd(self, program, note, v, phase, pitch, **kwargs):
        abs_phase = (phase - 64) / 32  # Convent [0 <= int <= 127] to [-2 <= float <= 2].
        return f"execute as @a at @s run playsound {self.pack_name}.{self.inst_name}.{note} voice @s ^{-abs_phase} ^ ^{2 - abs(abs_phase)} {v / 255} {pitch}"

    def get_stop_cmd(self, program, note, **kwargs):
        if not self.use_stop:
            return None

        return f"execute as @a at @s run stopsound {self.pack_name}.{self.inst_name}.{note} voice @s"
