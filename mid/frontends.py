import logging
from math import floor

from base.command_types import *


class Frontend(object):
    def __init__(self):
        pass

    def get_play_cmd(self, **kwargs) -> str:
        pass

    def get_stop_cmd(self, **kwargs) -> str:
        pass


class WorkerXG(Frontend):
    """The *RECOMMENDED* frontend for project MCDI."""

    __author__ = "kworker"

    def __init__(self,
                 use_stop: "Use the stopsound command" = True,
                 use_drum: "Use the MIDI drum channel" = True,
                 stop_drum: "Use stopsound for drum" = False):

        super(WorkerXG, self).__init__()
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum

    def get_play_cmd(self, ch, program, note, v, phase, pitch, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        abs_phase = (phase - 64) / 32  # Convert [0 <= int <= 127] to [-2 <= float <= 2].

        return Execute(
            PlaySound(
                f"xg.{program - 1 if program > 0 else 'drum'}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(-abs_phase, 0, 2 - abs(abs_phase)),
                velocity=v / 255, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, program, note, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        return Execute(
            StopSound(
                f"xg.{program - 1 if program > 0 else 'drum'}.{note}",
                channel="voice", for_="@s",
            ),
            as_="@a", at="@s"
        )


class Soma(Frontend):
    """The fundamental frontend for project MCDI."""

    __author__ = "kworker"

    LONG_SAFE = (  # These are the long notes.
        1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        38, 39, 40, 41, 42, 43, 44, 45, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 120
    )

    def __init__(self,
                 use_stop: "Use the stopsound command" = True,
                 use_drum: "Use the MIDI drum channel" = True,
                 stop_drum: "Use stopsound for drum" = False):

        super(Soma, self).__init__()
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum

    def get_play_cmd(self, ch, program, note, v, phase, pitch, long, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        abs_phase = (phase - 64) / 32  # Convert [0 <= int <= 127] to [-2 <= float <= 2].

        return Execute(
            PlaySound(
                f"{str(program) + 'c' * (program in self.LONG_SAFE and long)}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(-abs_phase, 0, 2 - abs(abs_phase)),
                velocity=v / 255, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, program, note, long, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        return Execute(
            StopSound(
                f"{str(program) + 'c' * (program in self.LONG_SAFE and long)}.{note}",
                channel="voice", for_="@s",
            ),
            as_="@a", at="@s"
        )


class Vanilla(Frontend):
    """The vanilla frontend for project MCDI."""

    __author__ = "HydrogenC"

    pitches = (  # These are the pitches in two octaves
        0.5, 0.529732, 0.561231, 0.594604, 0.629961, 0.667420, 0.707107, 0.749154, 0.793701, 0.840896, 0.890899,
        0.943874, 1, 1.059463, 1.122462, 1.189207, 1.259921, 1.334840, 1.414214, 1.498307, 1.587401, 1.681793, 1.781797,
        1.887749, 2
    )

    insts_pitch = {
        "bass": 1, "bell": 5, "flute": 4, "chime": 5, "guitar": 2, "xylophone": 5, "iron_xylophone": 3, "cow_bell": 4,
        "didgeridoo": 1, "bit": 3, "banjo": 3, "pling": 3, "harp": 3
    }

    def __init__(self,
                 f1_inst: "Instrument to play F#1-F#2 with" = "bass",
                 f2_inst: "Instrument to play F#2-F#3 with" = "bass",
                 f3_inst: "Instrument to play F#3-F#4 with" = "harp",
                 f4_inst: "Instrument to play F#4-F#5 with" = "harp",
                 f5_inst: "Instrument to play F#5-F#6 with" = "bell",
                 f6_inst: "Instrument to play F#6-F#7 with" = "bell",
                 use_stop: "Use the stopsound command" = True,
                 use_drum: "Use the MIDI drum channel" = False,
                 stop_drum: "Use stopsound for drum" = False):

        super(Vanilla, self).__init__()
        self.insts = f1_inst, f2_inst, f3_inst, f4_inst, f5_inst, f6_inst
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum

        for i, inst in enumerate(self.insts):
            if inst not in self.insts:
                raise ValueError(f"Instrument name not in {self.insts_pitch.keys()}: {inst}")
            if self.insts_pitch[inst] > (i + 1) or (self.insts_pitch[inst] + 2) < (i + 1):
                raise ValueError(f"Instrument does not cover the specified range: {inst}")

    def get_play_cmd(self, ch, note, v, phase, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        if note < 18 or note > 90:
            logging.warning(f"On note {note} at channel{ch} out of range! ")
            return None

        abs_phase = (phase - 64) / 32  # Convert [0 <= int <= 127] to [-2 <= float <= 2].

        inst_index = floor(((note - 18) / 12) if note != 90 else 5)  # Get the instrument to use(in range)
        base_pitch = self.insts_pitch[(inst := self.insts[inst_index])]  # Get the pitch for the instrument

        return Execute(
            PlaySound(
                f"minecraft:block.note_block.{inst}",
                channel="voice", for_="@s",
                position=LocalPosition(-abs_phase, 0, 2 - abs(abs_phase)),
                velocity=v / 255, pitch=self.pitches[note - base_pitch * 18],
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, note, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        if note < 18 or note > 90:
            logging.warning(f"Off note {note} at channel{ch} out of range! ")
            return None

        inst_index = floor(((note - 18) / 12) if note != 90 else 5)  # Get the instrument to use(in range)
        base_pitch = self.insts_pitch[(inst := self.insts[inst_index])]  # Get the pitch for the instrument

        return Execute(
            StopSound(
                f"minecraft:block.note_block.{inst}",
                channel="voice", for_="@s",
            ),
            as_="@a", at="@s"
        )


class Mcrg(Frontend):
    """The auto-tune remix frontend for project MCDI."""

    __author__ = "HydrogenC"

    def __init__(self,
                 pack_name: "Name of the target resourcepack" = "mcrg",
                 inst_name: "Name of the target instrument" = "inst",
                 use_stop: "Use the stopsound command" = True,
                 use_drum: "Use the MIDI drum channel" = False,
                 stop_drum: "Use stopsound for drum" = False):

        super(Mcrg, self).__init__()
        self.pack_name = pack_name
        self.inst_name = inst_name
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum

    def get_play_cmd(self, ch, program, note, v, phase, pitch, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        abs_phase = (phase - 64) / 32  # Convert [0 <= int <= 127] to [-2 <= float <= 2].

        return Execute(
            PlaySound(
                f"{self.pack_name}.{self.inst_name}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(-abs_phase, 0, 2 - abs(abs_phase)),
                velocity=v / 255, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, program, note, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        return Execute(
            PlaySound(
                f"{self.pack_name}.{self.inst_name}.{note}",
                channel="voice", for_="@s",
            ),
            as_="@a", at="@s"
        )