import json
import logging
import os
from math import floor, radians, sin, cos

from base.command_types import *
from mid.core import InGameGenerator


def get_phase_point(t, r):
    i = radians(abs(t) + 90)
    rx, ry = cos(i), sin(i)
    dx, dy = rx * r, ry * r

    if t < 0:
        return dx, dy
    return -dx, dy


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

    def __init__(self, parent: InGameGenerator,
                 use_stop: "Use the stopsound command." = True,
                 use_drum: "Use the MIDI drum channel." = True,
                 stop_drum: "Use stopsound for drum." = True,
                 drum_stop_delay: "How long to delay stopsound for drum." = 40,
                 use_old_context: "Use old context when fading a note," = True):

        super(WorkerXG, self).__init__()
        self.parent = parent
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum
        self.drum_stop_delay = drum_stop_delay
        self.use_old_context = use_old_context

        with open(os.path.join(os.path.split(__file__)[0], "workerxg.json")) as file:
            self.mapping = json.load(file)

    def get_play_cmd(self, ch, note, program, v, phase, pitch, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        x, y = get_phase_point((phase - 64) / 64 * 90, 2)

        return Execute(
            PlaySound(
                f"xg.{program - 1 if program > 0 else 'drum'}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(x, 0, y),
                velocity=v / 127, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, note, program, phase, linked, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        if linked is not None:
            duration = round((linked[0] - linked[1]) / self.parent.tick_rate * self.parent.tick_scale * 20)

            if 1 <= duration <= 160 and program != 0:
                if self.use_old_context:
                    program_mapping, volume_mapping, phase_mapping, pitch_mapping = linked[2].context

                    if linked[2].channel in volume_mapping.keys() and self.parent.gvol_enabled:  # Set volume
                        volume = volume_mapping[linked[2].channel]["value"] / 127
                    else:
                        volume = 1  # Max volume

                    volume_value = volume * linked[2].velocity * self.parent.volume_factor

                    if linked[2].channel in pitch_mapping.keys() and self.parent.pitch_enabled:  # Set pitch
                        pitch = pitch_mapping[linked[2].channel]["value"]
                    else:
                        pitch = self.parent.pitch_base  # No pitch

                    pitch_value = 2 ** ((pitch / self.parent.pitch_base - 1) * self.parent.pitch_factor / 12)

                    if linked[2].channel in phase_mapping.keys() and self.parent.phase_enabled:  # Set phase
                        phase = phase_mapping[linked[2].channel]["value"]
                    else:
                        phase = 64  # Middle phase

                else:
                    volume_value, pitch_value = 127, 1

                v = self.mapping[program - 1][note][duration - 1]
                x, y = get_phase_point((phase - 64) / 64 * 90, 2)
                abv = v * volume_value / 127

                self.parent.schedule(0, Execute(
                    PlaySound(
                        f"xg.f{program - 1}.{note}",
                        channel="voice", for_="@s",
                        position=LocalPosition(x, 0, y),
                        velocity=abv, pitch=pitch_value,
                    ),
                    as_="@a", at="@s"
                ))

        if program > 0:
            return Execute(
                StopSound(
                    f"xg.{program - 1}.{note}",
                    channel="voice", for_="@s",
                ),
                as_="@a", at="@s"
            )
        else:
            self.parent.schedule(self.drum_stop_delay, Execute(
                StopSound(
                    f"xg.drum.{note}",
                    channel="voice", for_="@s",
                ),
                as_="@a", at="@s"
            ))


class Soma(Frontend):
    """The fundamental frontend for project MCDI."""

    __author__ = "kworker"

    LONG_SAFE = (  # These are the long notes.
        1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
        38, 39, 40, 41, 42, 43, 44, 45, 49, 50, 51, 52, 53, 54, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
        69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95,
        96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 110, 111, 112, 120
    )

    def __init__(self, parent: InGameGenerator,
                 use_stop: "Use the stopsound command." = True,
                 use_drum: "Use the MIDI drum channel." = True,
                 stop_drum: "Use stopsound for drum." = True,
                 threshold: "The threshold for long notes." = 40):

        super(Soma, self).__init__()
        self.parent = parent
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum
        self.threshold = threshold

    def get_play_cmd(self, ch, note, program, v, phase, pitch, linked, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        long = linked[0] - linked[1] > self.threshold if linked is not None else False
        x, y = get_phase_point((phase - 64) / 64 * 90, 2)

        return Execute(
            PlaySound(
                f"{str(program) + 'c' * (program in self.LONG_SAFE and long)}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(x, 0, y),
                velocity=v / 127, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, note, program, linked, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        long = linked[0] - linked[1] > self.threshold if linked is not None else False

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


class Mcrg(Frontend):
    """The auto-tune remix frontend for project MCDI."""

    __author__ = "HydrogenC"

    def __init__(self, parent: InGameGenerator,
                 pack_name: "Name of the target namespace." = "mcrg",
                 inst_name: "Name of the target instrument." = "inst",
                 use_stop: "Use the stopsound command." = True,
                 use_drum: "Use the MIDI drum channel." = True,
                 stop_drum: "Use stopsound for drum." = True):

        super(Mcrg, self).__init__()
        self.parent = parent
        self.pack_name = pack_name
        self.inst_name = inst_name
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum

    def get_play_cmd(self, ch, note, program, v, phase, pitch, **kwargs):
        if not self.use_drum and ch == 9:
            return None

        x, y = get_phase_point((phase - 64) / 64 * 90, 2)

        return Execute(
            PlaySound(
                f"{self.pack_name}.{self.inst_name}.{note}",
                channel="voice", for_="@s",
                position=LocalPosition(x, 0, y),
                velocity=v / 127, pitch=pitch,
            ),
            as_="@a", at="@s"
        )

    def get_stop_cmd(self, ch, note, program, **kwargs):
        if not self.use_stop or (not self.use_drum and ch == 9) or (not self.stop_drum and ch == 9):
            return None

        return Execute(
            PlaySound(
                f"{self.pack_name}.{self.inst_name}.{note}",
                channel="voice", for_="@s",
            ),
            as_="@a", at="@s"
        )
