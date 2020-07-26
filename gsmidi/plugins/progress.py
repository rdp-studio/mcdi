from gsmidi.core import Generator
from gsmidi.plugins import Plugin


class Progress(Plugin):
    __author__ = "kworker"
    __doc__ = """Simply shows a progress bar, useful for video making"""

    def __init__(self,
                 pk: "The ID for the bossbar. For professional users only." = 0,
                 text: "The title for the bossbar to show on the top." = "MCDI",
                 color: "The color for the bossbar and the title." = "yellow"):
        self.pk = pk
        self.text = text
        self.color = color

    def exec(self, generator: Generator):
        if generator.is_first_tick:
            generator.set_tick_command(f'bossbar add {self.pk} {{"text": "{self.text}"}}')
            generator.set_tick_command(command=f"bossbar set {self.pk} color {self.color}")
            generator.set_tick_command(command=f"bossbar set {self.pk} max {generator.loaded_tick_count}")
            generator.set_tick_command(command=f"bossbar set {self.pk} players @a")
            generator.set_tick_command(command=f"bossbar set {self.pk} visible true")
            return None
        if generator.is_last_tick:
            generator.set_tick_command(command=f"bossbar set {self.pk} visible false")
            return None
        generator.set_tick_command(command=f"bossbar set {self.pk} value {generator.tick_index}")
