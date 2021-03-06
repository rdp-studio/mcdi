import re

from mid.core import BaseCbGenerator
from mid.plugins import Plugin


class Lyric(Plugin):
    __author__ = "kworker"
    __doc__ = """Lyric generated by .lrc files."""

    def __init__(self,
                 fp: "The path of the *.lrc file.",
                 offset: "Move the timeline of the lyric forward(or backward)" = 0,
                 style: '"title" or "subtitle"(default) or "actionbar"' = "subtitle"):
        self.lyric_ticks = {}
        self.style = style if style in (
            "title", "subtitle", "actionbar"
        ) else "subtitle"

        with open(fp, "r", encoding="utf8") as lyric:  # Open lyric file
            lyric_lines = lyric.readlines()

        for line_number, lyric_line in enumerate(lyric_lines):
            if match := re.findall(r"\[(\d\d):(\d\d)\.(\d\d)]\s?(.*)\n?", lyric_line):
                m, s, ms, lyric = match[0]  # Unpack tuple
            elif match := re.findall(r"\[(ti|ar|al|by|offset):.+?\].*\n?", lyric_line):
                continue  # Ignore these meta messages
            elif not lyric_line.strip():
                continue  # Ignore these blank lines
            else:
                raise SyntaxError(f"Malformed LRC syntax in line {line_number}.")

            self.lyric_ticks[round((int(m) * 60 + int(s) + int(ms) / 100) * 20) + offset] = lyric

    def exec(self, generator: BaseCbGenerator):
        if generator.tick_index in self.lyric_ticks.keys():  # Add a line of lyric, shows in actionbar
            if self.style == "title":
                generator.add_tick_command(command=f'title @a title "{self.lyric_ticks[generator.tick_index]}"')

            elif self.style == "subtitle":
                generator.add_tick_command(command=f'title @a title ""')  # Placeholder to make the subtitle visible
                generator.add_tick_command(command=f'title @a subtitle "{self.lyric_ticks[generator.tick_index]}"')

            elif self.style == "actionbar":
                generator.add_tick_command(command=f'title @a actionbar "{self.lyric_ticks[generator.tick_index]}"')
