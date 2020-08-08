from base.minecraft_types import *
from gsmidi.core import Generator
from gsmidi.plugins import Plugin


class MusicTitle(Plugin):
    __author__ = "kworker"
    __doc__ = """Title at the beginning and the end, useful for video making"""

    DEFAULT_IN_TITLE = {
        "text": "Codename: MCDI",
        "color": "green"
    }
    DEFAULT_IN_SUBTITLE = {
        "text": "By kworker (Frank Yang)"
    }
    DEFAULT_OUT_TITLE = {
        "text": "谢谢你看完这个视频!",
        "color": "red"
    }
    DEFAULT_OUT_SUBTITLE = {
        "text": "喜欢就给我个三连吧~"
    }

    def __init__(self,
                 in_title: "The big title when the music starts." = None,
                 in_subtitle: "The small title when the music starts." = None,
                 out_title: "The big title when the music ends." = None,
                 out_subtitle: "The small title when the music ends." = None):
        self.in_title = in_title if in_title is not None else self.DEFAULT_IN_TITLE
        self.in_subtitle = in_subtitle if in_subtitle is not None else self.DEFAULT_IN_SUBTITLE
        self.out_title = out_title if out_title is not None else self.DEFAULT_OUT_TITLE
        self.out_subtitle = out_subtitle if out_subtitle is not None else self.DEFAULT_OUT_SUBTITLE

    def exec(self, generator: Generator):
        if generator.is_first_tick:  # At the beginning
            generator.add_tick_command(command=f"title @a title {json.dumps(self.in_title, ensure_ascii=False)}")
            generator.add_tick_command(command=f"title @a subtitle {json.dumps(self.in_subtitle, ensure_ascii=False)}")
        elif generator.is_last_tick:  # At the end
            generator.add_tick_command(command=f"title @a title {json.dumps(self.out_title, ensure_ascii=False)}")
            generator.add_tick_command(command=f"title @a subtitle {json.dumps(self.out_subtitle, ensure_ascii=False)}")


class CopyrightTitle(Plugin):
    __author__ = "kworker"
    __doc__ = """Title throughout the music, useful for video making"""

    def __init__(self,
                 text: "The copyright information throughout the music."):
        self.text = text

    def exec(self, generator: Generator):
        generator.add_tick_command(command=f"title @a actionbar {json.dumps(self.text, ensure_ascii=False)}")