from base.minecraft_types import *
from mid.core import BaseCbGenerator
from mid.plugins import Plugin


class FixedTime(Plugin):
    __author__ = "kworker"
    __doc__ = """Allows you to have a fixed time while playing the music."""

    def __init__(self,
                 value: "The time(in tick) to fix."):
        self.value = value

    def init(self, generator: BaseCbGenerator):
        generator.built_function.append("gamerule doDaylightCycle false")
        generator.built_function.append(f"time set {self.value}")


class FixedRain(Plugin):
    __author__ = "kworker"
    __doc__ = """Allows you to have a fixed rain while playing the music."""

    def __init__(self,
                 value: "The weather name to fix."):
        self.value = value

    def init(self, generator: BaseCbGenerator):
        generator.built_function.append("gamerule doWeatherCycle false")
        generator.built_function.append(f"weather {self.value}")


class Viewport(Plugin):
    __author__ = "kworker"
    __doc__ = """Fixed or initial viewport for players."""

    PRESET1 = [-16, 32, 64, 0, 16, 64]
    PRESET2 = [-24, 48, 64, 0, 24, 64]
    PRESET3 = [24, 32, 1, 48, 8, 96]

    def __init__(self,
                 x: "The initial relative x-axis of the viewport.",
                 y: "The initial relative y-axis of the viewport.",
                 z: "The initial relative z-axis of the viewport.",
                 fx: "The initial relative facing in x-axis of the viewport.",
                 fy: "The initial relative facing in y-axis of the viewport.",
                 fz: "The initial relative facing in z-axis of the viewport."):
        self.position = x, y, z
        self.facing = fx, fy, fz

    def exec(self, generator: BaseCbGenerator):
        x, y, z = self.position
        fx, fy, fz = self.facing
        y -= generator.y_axis_index
        fy -= generator.y_axis_index
        generator.add_tick_command(command=f"tp @a ~{x} ~{y} ~{z} facing ~{fx} ~{fy} ~{fz}")


class PigPort(Plugin):
    __author__ = "kworker"
    __doc__ = """Fixed or initial viewport riding pigs."""

    PRESET1 = [-16, 32, 64, 0, 16, 64]
    PRESET2 = [-24, 48, 64, 0, 24, 64]
    PRESET3 = [24, 32, 1, 48, 8, 96]

    def __init__(self,
                 x: "The initial relative x-axis of the viewport.",
                 y: "The initial relative y-axis of the viewport.",
                 z: "The initial relative z-axis of the viewport.",
                 fx: "The initial relative facing in x-axis of the viewport.",
                 fy: "The initial relative facing in y-axis of the viewport.",
                 fz: "The initial relative facing in z-axis of the viewport."):
        self.position = x, y, z
        self.facing = fx, fy, fz

    def init(self, generator: BaseCbGenerator):
        function = Function(generator.namespace, "summon_pig")
        function.extend(
            ["summon minecraft:pig ~-1 ~1 ~-1 {Saddle: 1b, NoGravity: 1b, NoAI: 1b, Silent: 1b, CustomName: '\"PP\"'}",
             "effect give @e[type=minecraft:pig,name=PP] minecraft:invisibility 1000000 1 true"])
        generator.initial_functions.append(function)

    def exec(self, generator: BaseCbGenerator):
        x, y, z = self.position
        fx, fy, fz = self.facing
        y -= generator.y_axis_index
        fy -= generator.y_axis_index
        generator.add_tick_command(command=f"tp @e[type=minecraft:pig,name=PP] ~{x} ~{y} ~{z}")


class ProgressBar(Plugin):
    __author__ = "kworker"
    __doc__ = """Just a progress bar."""

    def __init__(self,
                 pk: "The ID for the bossbar. For professional users only." = 0,
                 text: "The title for the bossbar to show on the top." = "MCDI",
                 color: "The color for the bossbar and the title." = "yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator: BaseCbGenerator):
        if generator.is_first_tick:
            generator.add_tick_command(f'bossbar add {self.pk} {{"text": "{self.text}"}}')
            generator.add_tick_command(command=f"bossbar set {self.pk} color {self.color}")
            generator.add_tick_command(command=f"bossbar set {self.pk} max {generator.loaded_tick_count}")
            generator.add_tick_command(command=f"bossbar set {self.pk} players @a")
            generator.add_tick_command(command=f"bossbar set {self.pk} visible true")
            return None
        if generator.is_last_tick:
            generator.add_tick_command(command=f"bossbar set {self.pk} visible false")
            return None
        generator.add_tick_command(command=f"bossbar set {self.pk} value {generator.tick_index}")
