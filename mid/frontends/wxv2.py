import json
import os

from base.command_types import *
from mid.core import InGameGenerator
from mid.frontends import *


class WorkerXG(Frontend):
    """The *RECOMMENDED* frontend for project MCDI."""

    __author__ = "kworker"

    def __init__(self, parent: InGameGenerator,
                 use_stop: "Use the stopsound command." = True,
                 use_drum: "Use the MIDI drum channel." = True,
                 stop_drum: "Use stopsound for drum." = False,
                 drum_stop_delay: "How long to delay stopsound for drum." = 40,
                 use_old_context: "Use old context when fading a note." = True):

        super(WorkerXG, self).__init__()
        self.parent = parent
        self.use_stop = use_stop
        self.use_drum = use_drum
        self.stop_drum = stop_drum
        self.drum_stop_delay = drum_stop_delay
        self.use_old_context = use_old_context

        with open(os.path.join(os.path.split(__file__)[0], "wxlm.json")) as file:
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