"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
import pickle
from abc import abstractmethod
from base64 import b64encode
from collections import deque
from math import ceil, floor
from operator import itemgetter
from random import randint

from mido import MidiFile, merge_tracks, tick2second

from base.command_types import *
from base.minecraft_types import *


def frange(start, stop, step):
    while start < stop:
        yield start
        start += step


def rand_function(namespace):
    return Function(
        namespace, randint(0, 2 ** 63 - 1)
    )


class BaseGenerator(MidiFile):
    STRING_UNSAFE = {
        "\n": r'\n',
        "\\": r"\\",
        r'"': r'\"',
    }

    def __init__(self, fp, namespace="mcdi", identifier="music"):
        logging.debug("Initializing generator...")

        super(BaseGenerator, self).__init__(fp)

        self.wrap_length = 128
        self.blank_ticks = 0
        self.tick_rate = 20
        self.tick_scale = 1
        self.namespace = namespace
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
        # Function stuffs
        self.loaded_messages = deque()
        self.built_function = Function(
            namespace, identifier
        )
        self.initial_functions = list()
        self.extended_functions = list()
        # Tick packages
        self._use_function_array = False  # * Experimental *
        self._current_tick_pkg = rand_function(self.namespace)

        self.merged_tracks = merge_tracks(
            self.tracks
        )  # Preload tracks for speed
        vars(self)["length"] = self.length

        self.tempo = 5e5

    def auto_tick_rate(self, duration=None, tolerance=5, step=.025, base=20, strict=False):
        if not duration:  # Calculate the length myself
            duration = self.length

        logging.info("Calculating maximum and minimum tick rate.")

        max_allow = base + base * (tolerance / duration)  # Max acceptable tick rate
        min_allow = base - base * (tolerance / duration)  # Min acceptable tick rate
        logging.debug(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1  # No bigger than 1 possible
        best_tick_rate = base  # The no-choice fallback
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

    def write_datapack(self, *args, **kwargs):
        # Reduces lag
        self.built_function.append(f"gamerule commandBlockOutput false")
        self.built_function.append(f"gamerule sendCommandFeedback false")

        logging.info(f"Writing {len(self.built_function)} command(s) built.")

        for i, function in enumerate(self.initial_functions):  # These runs with the build func.
            self.built_function.append(f"function {function.namespace}:{function.identifier}")

        self.built_function.to_pack(*args, **kwargs)  # Save to datapack

        for function in self.initial_functions + self.extended_functions:
            function.to_pack(*args, **kwargs)  # Save these to datapack

        logging.info("Write procedure finished. Now enjoy your music!")

    def _add_tick_package(self):
        self.extended_functions.append(pkg := self._current_tick_pkg)
        self._set_command_block(
            command=f"function {self.namespace}:{pkg.identifier}"
        )
        self._current_tick_pkg = rand_function(self.namespace)

    def add_tick_command(self, command=None, *args, **kwargs):
        if self._use_function_array:  # Use functions to build music
            return self._current_tick_pkg.append(command=command)
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

        self.built_function.append(
            f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{"chain_" if chain else ""}command_block[facing={facing}]{{auto:{"true" if auto else "false"},Command:"{command}",LastOutput:false,TrackOutput:false}} replace'
        )

        self.axis_y_index += 1

    def __iter__(self):
        if self.type == 2:
            raise TypeError("can't merge tracks in type 2 (asynchronous) file")

        tempo = 5e5
        for msg in self.merged_tracks:
            delta = tick2second(msg.time, self.ticks_per_beat, tempo) if msg.time > 0 else 0

            yield msg.copy(time=delta)

            if msg.type == 'set_tempo':
                tempo = msg.tempo

    @property
    def use_function_array(self):
        return self._use_function_array

    @use_function_array.setter
    def use_function_array(self, value):
        if value:
            warnings.warn(RuntimeWarning(
                "Function array is a unstable feature and you may *NOT* commit a issue for that."
            ))
        self._use_function_array = value

    # Plugin APIs

    @abstractmethod
    def on_notes(self):
        pass

    @abstractmethod
    def off_notes(self):
        pass

    @abstractmethod
    def current_on_notes(self):
        pass

    @abstractmethod
    def current_off_notes(self):
        pass

    @abstractmethod
    def future_on_notes(self, tick):
        pass


class InGameGenerator(BaseGenerator):
    def __init__(self, frontend, plugins=None, middles=None, *args, **kwargs):
        if plugins is None:
            plugins = []
        if middles is None:
            middles = []

        self.plugins = list(plugins)
        self.middles = list(middles)

        super(InGameGenerator, self).__init__(*args, **kwargs)

        self.frontend = frontend

        # Load variables
        self.prog_enabled = True
        self.gvol_enabled = True
        self.pan_enabled = True
        self.pitch_enabled = False
        self.volume_factor = 1
        self.pitch_factor = 2
        self.pitch_base = 8192

        self.long_flags = []
        self.half_flags = []

    def long_note_analysis(self, threshold=40, ignore=()):
        logging.debug("Analysing long notes.")

        # Clear analysed items
        self.long_flags.clear()

        sustain_msgs, timestamp = [], 0

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

        # Clear analysed items
        self.half_flags.clear()

        sustain_msgs, timestamp = [], 0

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
        logging.debug("Loading message(s) from the MIDI file.")

        for middle in self.middles:
            for dependency in middle.__dependencies__:
                assert dependency in tuple(
                    map(type, self.middles)), f"Dependency {dependency} of {middle} is required, but not found."
            for conflict in middle.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.middles)), f"Conflict {conflict} of {middle} is strictly forbidden, but found."
            middle.init(self)

        # Clear loaded items
        self.loaded_messages.clear()
        timestamp = message_count = 0

        program_mapping, volume_mapping, phase_mapping, pitch_mapping = {}, {}, {}, {}

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

            tick_time = round(
                (timestamp + message.time) * self.tick_rate / self.tick_scale
            )
            self.loaded_tick_count = max(self.loaded_tick_count, tick_time)

            if "note" in message.type:  # Note_on / note_off
                if message.channel in program_mapping.keys() and self.prog_enabled:  # Set program
                    program = program_mapping[message.channel]["value"] + 1
                else:
                    program = 1

                if message.channel in volume_mapping.keys() and self.gvol_enabled:  # Set volume
                    volume = volume_mapping[message.channel]["value"] / 127
                else:
                    volume = 1  # Max volume

                volume_value = volume * message.velocity * self.volume_factor

                if message.channel in phase_mapping.keys() and self.pan_enabled:  # Set program
                    phase_value = phase_mapping[message.channel]["value"]
                else:
                    phase_value = 64  # Middle phase

                if message.channel in pitch_mapping.keys() and self.pitch_enabled:  # Set pitch
                    pitch = pitch_mapping[message.channel]["value"]
                else:
                    pitch = self.pitch_base  # No pitch

                pitch_value = 2 ** ((pitch / self.pitch_base - 1) * self.pitch_factor / 12)

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
                program_mapping[message.channel] = {"value": message.program, "time": tick_time}

            elif "control" in message.type:

                if message.control == 7:  # Volume change
                    volume_mapping[message.channel] = {"value": message.value, "time": tick_time}

                elif message.control == 121:  # No volume change
                    volume_mapping[message.channel] = {"value": 1.0, "time": tick_time}  # Recover

                elif message.control == 10:  # Phase change
                    phase_mapping[message.channel] = {"value": message.value, "time": tick_time}

            elif "pitch" in message.type:  # Pitch change
                pitch_mapping[message.channel] = {"value": message.pitch, "time": tick_time}

            timestamp += message.time

            for middle in self.middles:  # Execute middleware
                middle.exec(self)

        self.loaded_messages = deque(sorted(self.loaded_messages, key=itemgetter("tick")))
        logging.info(f"Load procedure finished. {len(self.loaded_messages)} event(s) loaded.")

    def build_events(self):
        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        for plugin in self.plugins:
            for dependency in plugin.__dependencies__:
                assert dependency in tuple(
                    map(type, self.plugins)), f"Dependency {dependency} of {plugin} is required, but not found."
            for conflict in plugin.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.plugins)), f"Conflict {conflict} of {plugin} is strictly forbidden, but found."
            plugin.init(self)

        # Clear built items
        self.tick_cache.clear()
        self.built_tick_count = 0

        self.tick_index = 0
        self.axis_y_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.is_first_tick = self.is_last_tick = False

        self.built_function.clear()

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
                    self.add_tick_command(command=self.get_play_cmd(message))

                elif message["type"] == "note_off":
                    self.add_tick_command(command=self.get_stop_cmd(message))

            for plugin in self.plugins:  # Execute plugin
                plugin.exec(self)

            if self._use_function_array:
                self._add_tick_package()

            # Get ready for next tick
            self.built_tick_count += 1
            self.tick_cache.clear()
            self.axis_y_index = 0

            if self.tick_index % 100 == 0:  # Show progress
                logging.info(f"Built {self.tick_index} tick(s), {self.loaded_tick_count + 1} tick(s) in all.")

        logging.info(f"Build procedure finished. {len(self.built_function)} command(s) built.")

    def get_play_cmd(self, message):
        return self.frontend.get_play_cmd(**message)

    def get_stop_cmd(self, message):
        return self.frontend.get_stop_cmd(**message)

    # Plugin APIs

    def on_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_on", self.loaded_messages))  # Every tick

    def off_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_off", self.loaded_messages))  # Every tick

    def current_on_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_on", self.tick_cache))  # Only for this tick

    def current_off_notes(self):
        return tuple(filter(lambda message: message["type"] == "note_off", self.tick_cache))  # Only for this tick

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


class RealTimeGenerator(BaseGenerator):
    def __init__(self, plugins=None, *args, **kwargs):
        if plugins is None:
            plugins = []

        self.plugins = list(plugins)

        super(RealTimeGenerator, self).__init__(*args, **kwargs)

    def load_messages(self):
        logging.debug("Loading message(s) from the MIDI file.")

        # Clear loaded items
        self.loaded_messages.clear()
        timestamp = message_count = 0

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

            tick_time = round(
                (timestamp + message.time) * self.tick_rate / self.tick_scale
            )
            self.loaded_tick_count = max(self.loaded_tick_count, tick_time)

            message_count += 1

            pkl_message = b64encode(pickle.dumps(message)).decode()

            message_dict = {
                "msg": pkl_message,
                "tick": tick_time,
                "type": message.type,
            }

            if "note" in message.type:
                message_dict["raw"] = {
                    "type": message.type,
                    "ch": message.channel,
                    "note": message.note,
                    "tick": int(tick_time),
                    "v": 255,
                    "program": 0,
                    "phase": 64,
                    "pitch": 1,
                    "half": False,
                    "long": False
                }  # Compatibility for in-game plugins

            self.loaded_messages.append(message_dict)

            timestamp += message.time

        self.loaded_messages = deque(sorted(self.loaded_messages, key=itemgetter("tick")))
        logging.info(f"Load procedure finished. {len(self.loaded_messages)} event(s) loaded.")

    def build_events(self):
        logging.debug(f'Building {len(self.loaded_messages)} event(s).')

        for plugin in self.plugins:
            for dependency in plugin.__dependencies__:
                assert dependency in tuple(
                    map(type, self.plugins)), f"Dependency {dependency} of {plugin} is required, but not found."
            for conflict in plugin.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.plugins)), f"Conflict {conflict} of {plugin} is strictly forbidden, but found."
            plugin.init(self)

        # Clear built items
        self.tick_cache.clear()
        self.built_tick_count = 0

        self.tick_index = 0
        self.axis_y_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.is_first_tick = self.is_last_tick = False

        self.built_function.clear()

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
                self.add_tick_command(command=f"say pythonAccess={message['msg']}")

            for plugin in self.plugins:  # Execute plugin
                plugin.exec(self)

            if self._use_function_array:
                self._add_tick_package()

            # Get ready for next tick
            self.built_tick_count += 1
            self.tick_cache.clear()
            self.axis_y_index = 0

            if self.tick_index % 100 == 0:  # Show progress
                logging.info(f"Built {self.tick_index} tick(s), {self.loaded_tick_count + 1} tick(s) in all.")

        logging.info(f"Build procedure finished. {len(self.built_function)} command(s) built.")

    # Plugin APIs

    def on_notes(self):
        return tuple(map(itemgetter("raw"),
            filter(lambda message: message["type"] == "note_on", self.loaded_messages)
        )
        )  # Every tick

    def off_notes(self):
        return tuple(map(itemgetter("raw"),
            filter(lambda message: message["type"] == "note_off", self.loaded_messages)
        )
        )  # Every tick

    def current_on_notes(self):
        return tuple(map(itemgetter("raw"),
            filter(lambda message: message["type"] == "note_on", self.tick_cache)
        )
        )  # Only for this tick

    def current_off_notes(self):
        return tuple(map(itemgetter("raw"),
            filter(lambda message: message["type"] == "note_off", self.tick_cache)
        )
        )  # Only for this tick

    def future_on_notes(self, tick):
        for message in self.loaded_messages:
            if message["type"] != "note_on":
                continue
            if message["tick"] < tick:
                continue
            if message["tick"] == tick:
                yield message["raw"]
            if message["tick"] > tick:
                break


if __name__ == '__main__':
    from mid.plugins import progress, music_title, piano_roll, viewport

    logging.basicConfig(level=logging.DEBUG)

    generator = RealTimeGenerator(fp=r"D:\音乐\【完美佳作03】打上花火 - DAKAO × 米津玄师.mid", plugins=[
        piano_roll.PianoRoll(),
        viewport.Viewport(
            *viewport.Viewport.PRESET2
        ),
        progress.Progress(
            text="(。・∀・)ノ 进度条"
        ),
        music_title.MusicTitle(
            [
                {
                    "text": "Pre-release",
                    "color": "red"
                }
            ], {
                "text": "By kworker"
            }
        ),
    ])
    generator.auto_tick_rate()
    generator.load_messages()
    generator.build_events()
    generator.write_datapack(r"D:\Minecraft\Server\world")
