from base.command_types import *
from mid.core import InGameGenerator
from mid.frontends import *


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

        x, y = vector_build((phase - 64) / 64 * 90, 2)

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
