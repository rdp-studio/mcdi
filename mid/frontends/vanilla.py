import logging
from math import floor

from base.command_types import *
from mid.core import InGameGenerator
from mid.frontends import *


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

    def __init__(self, parent: InGameGenerator,
                 f1_inst: "Instrument to play F#1-F#2 with." = "bass",
                 f2_inst: "Instrument to play F#2-F#3 with." = "bass",
                 f3_inst: "Instrument to play F#3-F#4 with." = "harp",
                 f4_inst: "Instrument to play F#4-F#5 with." = "harp",
                 f5_inst: "Instrument to play F#5-F#6 with." = "bell",
                 f6_inst: "Instrument to play F#6-F#7 with." = "bell",
                 use_stop: "Use the stopsound command." = True,
                 use_drum: "Use the MIDI drum channel." = True,
                 stop_drum: "Use stopsound for drum." = True):

        super(Vanilla, self).__init__()
        self.parent = parent
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

        x, y = get_phase_point((phase - 64) / 64 * 90, 2)

        inst_index = floor(((note - 18) / 12) if note != 90 else 5)  # Get the instrument to use(in range)
        base_pitch = self.insts_pitch[(inst := self.insts[inst_index])]  # Get the pitch for the instrument

        return Execute(
            PlaySound(
                f"minecraft:block.note_block.{inst}",
                channel="voice", for_="@s",
                position=LocalPosition(x, 0, y),
                velocity=v / 127, pitch=self.pitches[note - base_pitch * 18],
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
