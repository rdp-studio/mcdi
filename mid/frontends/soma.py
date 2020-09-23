from base.command_types import *
from mid.core import InGameGenerator
from mid.frontends import *


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
                 stop_drum: "Use stopsound for drum." = False,
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
