from gsmidi.core import Generator
from gsmidi.plugins import Plugin


class Viewport(Plugin):
    __author__ = "kworker"
    __doc__ = """Fixed or flexible viewport, useful for video making"""

    def __init__(self,
                 x: "The initial relative x-axis of the viewport." = -16,
                 y: "The initial relative y-axis of the viewport." = 32,
                 z: "The initial relative z-axis of the viewport." = 64,
                 fx: "The initial relative facing in x-axis of the viewport." = 0,
                 fy: "The initial relative facing in y-axis of the viewport." = 16,
                 fz: "The initial relative facing in z-axis of the viewport." = 64,
                 fixed: "Fix the player to the position during the music." = True):
        self.position = x, y, z
        self.facing = fx, fy, fz
        self.fixed = fixed

    def exec(self, generator: Generator):
        if self.fixed or generator.is_first_tick:  # Fixed viewport
            x, y, z = self.position
            fx, fy, fz = self.facing
            y -= generator.y_index
            fy -= generator.y_index
            generator.set_tick_command(command=f"tp @a ~{x} ~{y} ~{z} facing ~{fx} ~{fy} ~{fz}")
        else:  # Just move forward
            generator.set_tick_command(command=f"execute as @a at @s run tp @s ~1 ~ ~")
