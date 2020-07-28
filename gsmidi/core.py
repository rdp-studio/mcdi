"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
from collections import deque
from math import ceil, floor
from operator import itemgetter
from random import randint

from mido import MidiFile, Message

from base.minecraft_types import *


def frange(start, stop, step):
    while start < stop:
        yield start
        start += step


class MyMidiMessage(Message):
    half = False
    long = False


class Generator(MidiFile):
    STRING_UNSAFE = {
        "\n": r'\n',
        "\\": r"\\",
        r'"': r'\"',
    }

    def __init__(self, fp, frontend, namespace="mcdi", func="music", plugins=None, middles=None):
        if plugins is None:
            plugins = []
        if middles is None:
            middles = []

        logging.debug("Initializing generator...")

        super().__init__(fp)
        self.frontend = frontend
        self.wrap_length = 128
        self.blank_ticks = 0
        self.tick_rate = 20
        self.namespace = namespace
        self.plugins = list(plugins)
        self.middles = list(middles)

        # Build variables
        self.tick_index = 0
        self.tick_cache = list()
        # Plugin stuffs
        self.loaded_tick_count = 0
        self.built_tick_count = 0
        self.axis_y_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.wrap_state = False
        self.is_first_tick = self.is_last_tick = False
        # Load variables
        self.prog_enabled = True
        self.gvol_enabled = True
        self.pan_enabled = True
        self.pitch_enabled = True
        self.volume_factor = 1
        self.pitch_power = 1
        self.pitch_factor = 1
        # Function stuffs
        self.loaded_messages = deque()
        self.built_function = Function(namespace, func)
        self.initial_functions = list()
        self.extended_functions = list()
        # MIDI stuffs
        self.tempo = 5E5
        # Function identifier
        self.id = randint(0, 2 ** 31 - 1)

        self.long_flags = []
        self.half_flags = []

    def auto_tick_rate(self, duration=None, tolerance=5, step=0.01, strict=False):
        if not duration:  # Calculate the length myself
            duration = self.length

        logging.info("Calculating maximum and minimum tick rate.")

        max_allow = 20 + 20 * (tolerance / duration)  # Max acceptable tick rate
        min_allow = 20 - 20 * (tolerance / duration)  # Min acceptable tick rate
        logging.debug(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1  # No bigger than 1 possible
        best_tick_rate = 20  # The no-choice fallback
        maximum = floor(max_allow) if strict else max_allow  # Rounded max acceptable tick rate
        minimum = ceil(min_allow) if strict else min_allow  # Rounded min acceptable tick rate

        for i in frange(minimum, maximum, step):
            timestamp = message_count = round_diff_sum = 0

            for message in self:
                round_diff_sum += abs(round(raw := (timestamp * i)) - raw)
                timestamp += message.time
                message_count += 1
            round_diff_sum /= message_count

            if round_diff_sum < min_time_diff:
                min_time_diff = round_diff_sum
                best_tick_rate = float(i)

            logging.debug(f"Tick rate = {i}, round difference = {round_diff_sum}.")

        self.tick_rate = best_tick_rate

        logging.info(f"Tick rate calculation finished({best_tick_rate}).")

    def long_note_analysis(self, threshold=40, ignore=()):
        logging.debug("Analysing long notes.")
        sustain_msgs, timestamp = [], 0

        self.long_flags.clear()

        for index, message in enumerate(self):  # Iterate over messages
            timestamp += message.time * self.tick_rate

            if message.type == "note_on":
                vars(message)["on_time"] = timestamp
                vars(message)["ch_note"] = (
                    message.channel, message.note
                )
                vars(message)["long_index"] = index

                sustain_msgs.append(message)

            elif message.type == "note_off":
                old_msg = next(filter(lambda p: p.ch_note == (message.channel, message.note), sustain_msgs))

                if (threshold < timestamp - old_msg.on_time) and (old_msg.channel not in (9, *ignore)):
                    old_i = old_msg.long_index
                    self.long_flags.append(old_i)
                    self.long_flags.append(index)

                sustain_msgs.remove(old_msg)

        logging.info("Long notes analysis procedure finished.")

    def half_note_analysis(self, minimum=.33, maximum=.67):
        logging.debug("Analysing half notes.")
        sustain_msgs, timestamp = [], 0

        self.half_flags.clear()

        for index, message in enumerate(self):  # Iterate over messages
            timestamp += message.time * self.tick_rate

            if message.type == "note_on":
                vars(message)["on_time"] = timestamp
                vars(message)["ch_note"] = (
                    message.channel, message.note
                )
                vars(message)["half_index"] = index

                sustain_msgs.append(message)

            elif message.type == "note_off":
                old_msg = next(filter(lambda p: p.ch_note == (message.channel, message.note), sustain_msgs))

                if minimum < abs(round(float_ := old_msg.on_time * self.tick_rate) - float_) < maximum:
                    old_i = old_msg.half_index
                    self.half_flags.append(old_i)
                    self.half_flags.append(index)

                sustain_msgs.remove(old_msg)

        logging.info("Half notes analysis procedure finished.")

    def load_messages(self):
        for middle in self.middles:
            for dependency in middle.__dependencies__:
                assert dependency in tuple(
                    map(type, self.middles)), f"Dependency {dependency} of {middle} is required, but not found."
            for conflict in middle.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.middles)), f"Conflict {conflict} of {middle} is strictly forbidden, but found."
            middle.init(self)

        self.loaded_messages.clear()
        timestamp = message_count = 0

        program_set, volume_set, phase_set, pitch_set = {}, {}, {}, {}  # For control + program change assign

        for index, message in enumerate(self):
            if message.is_meta:
                if message.type == "set_tempo":
                    self.tempo = message.tempo
                elif message.type == "time_signature":
                    logging.debug(f"MIDI file timing info: {message.numerator}/{message.denominator}.")
                elif message.type == "key_signature":
                    logging.debug(f"MIDI file pitch info: {message.key}.")
                elif message.type in ("text", "copyright"):
                    logging.info(f"MIDI META message: {message.text}.")
                continue

            tick_time = round((timestamp + message.time) * self.tick_rate)
            self.loaded_tick_count = tick_time  # Real-time update~

            if "note" in message.type:  # Note_on / note_off
                if message.channel in program_set.keys() and self.prog_enabled:  # Set program
                    program = program_set[message.channel]["value"] + 1
                else:
                    program = 1

                if message.channel in volume_set.keys() and self.gvol_enabled:  # Set volume
                    volume = volume_set[message.channel]["value"] / 127
                else:
                    volume = 1  # Max volume

                volume_value = volume * message.velocity * self.volume_factor

                if message.channel in phase_set.keys() and self.pan_enabled:  # Set program
                    phase_value = phase_set[message.channel]["value"]
                else:
                    phase_value = 64  # Middle phase

                if message.channel in pitch_set.keys() and self.pitch_enabled:  # Set pitch
                    pitch = pitch_set[message.channel]["value"]
                else:
                    pitch = 1  # No pitch

                pitch_value = pitch ** self.pitch_power * self.pitch_factor

                if message.channel == 9:
                    program = 0  # Force drum

                long = index in self.long_flags
                half = index in self.half_flags
                if message.type == "note_off":
                    tick_time += half  # Bool to int

                self.loaded_messages.append({
                    "type": message.type,
                    "ch": message.channel,
                    "note": message.note,
                    "tick": int(tick_time),
                    "v": volume_value,
                    "program": program,
                    "phase": phase_value,
                    "pitch": pitch_value,
                    "half": half,
                    "long": long  # Convert message to dict object, for **kwargs.
                })

                message_count += 1

            elif "prog" in message.type:
                program_set[message.channel] = {"value": message.program, "time": tick_time}

            elif "control" in message.type:

                if message.control == 7:  # Volume change
                    volume_set[message.channel] = {"value": message.value, "time": tick_time}

                elif message.control == 121:  # No volume change
                    volume_set[message.channel] = {"value": 1.0, "time": tick_time}  # Recover

                elif message.control == 10:  # Phase change
                    phase_set[message.channel] = {"value": message.value, "time": tick_time}

            elif "pitch" in message.type:  # Pitch change
                pitch_set[message.channel] = {"value": message.pitch, "time": tick_time}

            timestamp += message.time

            for middle in self.middles:  # Execute middleware
                middle.exec(self)

        self.loaded_messages = deque(sorted(self.loaded_messages, key=itemgetter("tick")))
        logging.info(f"Load procedure finished. {len(self.loaded_messages)} event(s) loaded.")

    def build_events(self, progress_callback=lambda x, y: None):
        for plugin in self.plugins:
            for dependency in plugin.__dependencies__:
                assert dependency in tuple(
                    map(type, self.plugins)), f"Dependency {dependency} of {plugin} is required, but not found."
            for conflict in plugin.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.plugins)), f"Conflict {conflict} of {plugin} is strictly forbidden, but found."
            plugin.init(self)

        self.tick_index = 0
        self.tick_cache.clear()

        self.built_tick_count = 0
        self.axis_y_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.is_first_tick = self.is_last_tick = False

        self.built_function.clear()

        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        for self.tick_index in range(-self.blank_ticks, self.loaded_tick_count + 1):
            self.build_axis_index = self.built_tick_count % self.wrap_length  # For plugins
            self.wrap_axis_index = self.built_tick_count // self.wrap_length  # For plugins
            wrap_state = (self.built_tick_count + 1) % self.wrap_length == 0
            self.is_first_tick = self.is_last_tick = False

            if self.tick_index == -self.blank_ticks:
                self.is_first_tick = True
            if self.tick_index == self.loaded_tick_count:
                self.is_last_tick = True

            if wrap_state:
                self._set_command_block(  # Row to wrap
                    chain=0, auto=0, command=f"setblock ~{1 - self.wrap_length} ~-1 ~1 minecraft:redstone_block")
            else:
                self._set_command_block(  # Ordinary row
                    chain=0, auto=0, command="setblock ~1 ~-1 ~ minecraft:redstone_block")

            self._set_command_block(command="setblock ~ ~-2 ~ minecraft:air replace")  # Remove redstone block

            while (messages := self.loaded_messages) and messages[0]["tick"] == self.tick_index:
                self.tick_cache.append(self.loaded_messages.popleft())  # Deque object is used to improve performance

            for message in self.tick_cache:
                if message["type"] == "note_on":
                    self.set_tick_command(command=self.get_play_cmd(message))

                elif message["type"] == "note_off":
                    self.set_tick_command(command=self.get_stop_cmd(message))

            for plugin in self.plugins:  # Execute plugin
                plugin.exec(self)

            # Get ready for next tick
            self.built_tick_count += 1
            self.tick_cache.clear()
            self.axis_y_index = 0

            if self.tick_index % 100 == 0:  # Show progress
                logging.info(f"Built {self.tick_index} tick(s), {self.loaded_tick_count + 1} tick(s) in all.")
                progress_callback(self.tick_index, self.loaded_tick_count + 1)  # For GUI progressbar callback 

        logging.info(f"Build procedure finished. {len(self.built_function)} command(s) built.")

    def write_datapack(self, *args, **kwargs):
        # Reduces lag
        self.built_function.append(f"gamerule commandBlockOutput false")
        self.built_function.append(f"gamerule sendCommandFeedback false")

        logging.info(f"Writing {len(self.built_function)} command(s) built.")

        for i, function in enumerate(self.initial_functions):  # Schedule reduces lag, these runs with the build func.
            self.built_function.append(f"schedule function {function.namespace}:{function.identifier} {i + 1}s")

        self.built_function.to_pack(*args, **kwargs)  # Save to datapack

        for function in self.initial_functions + self.extended_functions:
            function.to_pack(*args, **kwargs)  # Save to datapack

        logging.info("Write procedure finished. Now enjoy your music!")

    def get_play_cmd(self, message):
        return self.frontend.get_play_cmd(**message)

    def get_stop_cmd(self, message):
        return self.frontend.get_stop_cmd(**message)

    def set_tick_command(self, command=None, *args, **kwargs):
        self._set_command_block(command=command, *args, **kwargs)

    def _set_command_block(self, x_shift=None, y_shift=None, z_shift=None, chain=1, auto=1, command=None, facing="up"):
        if x_shift is None:
            x_shift = self.build_axis_index
        if y_shift is None:
            y_shift = self.axis_y_index
        if z_shift is None:
            z_shift = self.wrap_axis_index
        if command is None:
            return None

        for unsafe, alternative in self.STRING_UNSAFE.items():
            command = str(command).replace(unsafe, alternative)

        setblock_cmd = f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{"chain_" if chain else ""}command_block[facing={facing}]{{auto:{"true" if auto else "false"},Command:"{command}",LastOutput:false,TrackOutput:false}} replace'
        self.built_function.append(setblock_cmd)

        self.axis_y_index += 1

    # Plugin APIs

    def on_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_on", self.loaded_messages))  # Every tick

    def current_on_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_on", self.tick_cache))  # Only for this tick

    def future_on_notes(self, tick):
        for message in self.loaded_messages:
            if message["type"] != "note_on":
                continue
            if message["tick"] < tick:
                continue
            if message["tick"] == tick:
                yield message
            if message["tick"] > tick:
                break


if __name__ == '__main__':
    from gsmidi.frontends import Soma
    from gsmidi.plugins import progress

    logging.basicConfig(level=logging.DEBUG)

    generator = Generator(r"D:\音乐\Only My Railgun(3).mid", Soma(), plugins=[
        # piano_roll.PianoRoll(),
        progress.Progress(
            text="(。・∀・)ノ 进度条"
        ),
        # viewport.Viewport(
        #     *viewport.Viewport.PRESET2
        # ),
        # large_title.LargeTitle({
        #     "text": "打上花火",
        #     "color": "red"
        # }, {
        #     "text": "By kworker"
        # }),
    ])
    # generator.auto_tick_rate()
    generator.long_note_analysis()
    # generator.half_note_analysis()
    generator.load_messages()
    generator.build_events()
    generator.write_datapack(r"D:\Minecraft\.minecraft\versions\1.14.4-forge-28.1.56\saves\MCDI")
