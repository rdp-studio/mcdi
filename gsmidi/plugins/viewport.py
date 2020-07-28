from gsmidi.core import Generator
from gsmidi.plugins import Plugin


class Viewport(Plugin):
    __author__ = "kworker"
    __doc__ = """Fixed or flexible viewport, useful for video making"""

    PRESET1 = [-16, 32, 64, 0, 16, 64]
    PRESET2 = [24, 32, 1, 48, 8, 96]

    def __init__(self,
                 x: "The initial relative x-axis of the viewport.",
                 y: "The initial relative y-axis of the viewport.",
                 z: "The initial relative z-axis of the viewport.",
                 fx: "The initial relative facing in x-axis of the viewport.",
                 fy: "The initial relative facing in y-axis of the viewport.",
                 fz: "The initial relative facing in z-axis of the viewport.",
                 fixed: "Fix the player to the position during the music." = True):
        self.position = x, y, z
        self.facing = fx, fy, fz
        self.fixed = fixed

    def exec(self, generator: Generator):
        if self.fixed or generator.is_first_tick:  # Fixed viewport
            x, y, z = self.position
            fx, fy, fz = self.facing
            y -= generator.axis_y_index
            fy -= generator.axis_y_index
            generator.set_tick_command(command=f"tp @a ~{x} ~{y} ~{z} facing ~{fx} ~{fy} ~{fz}")

        elif generator.warp_state:  # Just move forward
            generator.set_tick_command(command=f"execute as @a at @s run tp @s ~{1 - generator.wrap_length} ~ ~")
        else:
            generator.set_tick_command(command=f"execute as @a at @s run tp @s ~1 ~ ~")
