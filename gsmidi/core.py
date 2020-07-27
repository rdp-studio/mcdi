"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
from collections import deque
from math import ceil, floor
from math import inf
from random import randint

from mido import MidiFile

from base.minecraft_types import *


class Generator(MidiFile):
    STRING_UNSAFE = {
        "\n": r'\n',
        "\\": r"\\",
        r'"': r'\"',
    }

    def __init__(self, fp, frontend, namespace="mcdi", func="music", wrap_length=128, blank_ticks=0, tick_rate=50,
                 plugins=None, middles=None):
        if plugins is None:
            plugins = []
        if middles is None:
            middles = []
        logging.debug("Initializing generator...")
        super().__init__(fp)
        self.frontend = frontend
        self.wrap_length = wrap_length
        self.blank_ticks = blank_ticks
        self.tick_rate = tick_rate
        self.namespace = namespace
        self.plugins = list(plugins)
        self.middles = list(middles)

        self.tick_cache = list()
        self.built_tick_count = 0
        self.build_axis_index = 0
        self.gvol_enabled = True
        self.pan_enabled = True
        self.pitch_enabled = True
        self.pitch_factor = 1
        self.tick_index = 0
        self.loaded_tick_count = 0
        self.volume_factor = 1
        self.wrap_axis_index = 0
        self.y_index = 0
        self.is_first_tick = self.is_last_tick = False

        self.loaded_messages = deque()
        self.built_function = Function(namespace, func)
        self.initial_functions = list()
        self.extended_functions = list()
        self.tempo = 5E5

        self.id = randint(0, 2 ** 31 - 1)

    def tick_rate_analysis(self, duration=None, tolerance=5, step=0.05, strict=True):
        if not duration:  # Calculate the length itself
            duration = self.length

        logging.info("Analysing maximum and minimum tick rate.")

        max_tick = 0

        for _, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {_}: {track}.")
            accum = sum(map(lambda x: x.time, track))
            max_tick = max(max_tick, accum)

        max_allow = 1 / ((duration - tolerance) * 20 / max_tick)  # Max acceptable tick rate
        min_allow = 1 / ((duration + tolerance) * 20 / max_tick)  # Min acceptable tick rate
        logging.debug(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1  # No bigger than 1 possible
        best_tick_rate = 1 / (duration * 20 / max_tick)  # The no-choice fallback
        maximum = ceil(max_allow) if strict else max_allow  # Rounded max acceptable tick rate
        minimum = floor(min_allow) if strict else min_allow  # Rounded min acceptable tick rate
        i = minimum

        while i < maximum:
            logging.debug(f"Trying tick rate: {i} (gametick/MIDI tick).")
            message_count = round_diff_sum = 0  # Round difference

            for _, track in enumerate(self.tracks):
                timestamp = 0
                for message in track:
                    round_diff_sum += abs(round(raw := ((timestamp + message.time) / i)) - raw)  # Difference algorithm
                    timestamp += message.time
                    message_count += 1
            round_diff_sum /= message_count

            logging.debug(f"Average round difference for tick rate {i}: {round_diff_sum}.")
            if round_diff_sum < min_time_diff:  # Has the minimum round difference
                min_time_diff = round_diff_sum
                best_tick_rate = i

            i += step

        logging.info(f"The best tick rate found: {best_tick_rate}. Tick rate analysis procedure finished.")
        self.tick_rate = best_tick_rate

    def long_note_analysis(self, threshold=40, ignore=(), progress_callback=lambda x, y: None):
        logging.debug("Analysing long notes.")

        track_count, sustain_notes = len(self.tracks), []  # For progress calculation

        for track_index, track in enumerate(self.tracks):
            logging.info(f"Reading events from track {track_index}: {track}...")
            timestamp = 0

            for message in track:  # Iterate over messages
                timestamp += message.time
                tick = timestamp / self.tick_rate  # Tick index in float

                if message.type == "note_on" and message.channel not in (9, *ignore):  # Long condition
                    vars(message)["timestamp"], vars(message)["long"] = timestamp, False
                    sustain_notes.append(message)  # For future length calculation

                elif message.type == "note_off":
                    for off_note in filter(  # If going to cancel any on-note:
                            lambda x: x.channel == message.channel and x.note == message.note, sustain_notes
                    ):
                        long_assign = (timestamp - off_note.timestamp) / self.tick_rate >= threshold
                        vars(off_note)["long"] = vars(message)["long"] = long_assign  # Assign as long note

                        sustain_notes.remove(off_note)  # Remove from sustain list

            progress_callback(track_index, track_count)  # For GUI progressbar callback
            logging.debug(f"Analysed long notes in track {track_index}.")

        logging.info("Long notes analysis procedure finished.")

    def half_note_analysis(self, minimum=0.3, maximum=0.7, progress_callback=lambda x, y: None):
        logging.info("Analysing half-tick notes.")

        track_count, sustain_notes = len(self.tracks), []  # For progress calculation

        for track_index, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {track_index}: {track}...")
            timestamp = 0

            for message in track:  # Iterate over messages
                timestamp += message.time
                tick = timestamp / self.tick_rate  # Tick index in float

                if message.type == "note_on" and minimum < 1 - ceil(tick) + tick < maximum:  # Half condition
                    vars(message)["half"], vars(message)["shift"] = True, - (round(tick) > tick)
                    sustain_notes.append(message)  # For future off-note assignment

                elif message.type == "note_off":
                    for off_note in filter(  # If going to cancel any on-note:
                            lambda x: x.channel == message.channel and x.note == message.note, sustain_notes
                    ):
                        half_assign = True, bool(1 - ceil(tick := (timestamp / self.tick_rate)) + tick)
                        vars(message)["half"], vars(message)["shift"] = half_assign  # Assign as half note

                        sustain_notes.remove(off_note)  # Remove from sustain list

            progress_callback(track_index, track_count)  # For GUI progressbar callback
            logging.debug(f"Analysed half-tick notes in track {track_index}.")

        logging.info("Half-tick notes analysis procedure finished.")

    def load_messages(self, limitation=inf):
        for middle in self.middles:
            for dependency in middle.__dependencies__:
                assert dependency in tuple(
                    map(type, self.middles)), f"Dependency {dependency} of {middle} is required, but not found."
            for conflict in middle.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.middles)), f"Conflict {conflict} of {middle} is *PROHIBITED*, but found."
            middle.init(self)

        self.loaded_messages.clear()

        for i, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {i}: {track}...")
            timestamp = message_count = 0  # Limitation here for a MIDI track

            program_set, volume_set, phase_set, pitch_set = {}, {}, {}, {}  # For control + program change assign

            for message in track:
                if message_count > limitation:
                    break  # Limitation exceeds

                if message.is_meta:
                    if message.type == "end_of_track":
                        break
                    elif message.type == "set_tempo":
                        self.tempo = message.tempo
                    continue

                relative_time = float(timestamp + message.time)
                tick_time = round(relative_time / self.tick_rate)

                if "note" in message.type:  # Note_on / note_off
                    program = 1  # Default
                    if message.channel == 9:
                        program = 0  # Force drum
                    elif message.channel in program_set.keys():
                        program = program_set[message.channel]["value"] + 1

                    if message.channel in volume_set.keys() and self.gvol_enabled:  # Set volume
                        volume = volume_set[message.channel]["value"] / 127
                    else:
                        volume = 1  # Max volume
                    volume_value = volume * message.velocity * self.volume_factor

                    if message.channel in phase_set.keys() and self.pan_enabled:  # Set channel(program)
                        phase_value = phase_set[message.channel]["value"]
                    else:
                        phase_value = 64  # Middle phase

                    if message.channel in pitch_set.keys() and self.pitch_enabled:  # Set pitch
                        pitch_value = pitch_set[message.channel]["value"] * self.pitch_factor
                    else:
                        pitch_value = 1  # No pitch

                    long = hasattr(message, "long")
                    half = hasattr(message, "half")
                    if half:  # half-note-only shift
                        tick_time += message.shift

                    self.loaded_messages.append({
                        "type": message.type, "ch": message.channel, "note": message.note, "tick": tick_time,
                        "v": volume_value, "program": program, "phase": phase_value, "pitch": pitch_value,
                        "half": half, "long": long, "track": i,  # Convert message to dict object, for **kwargs.
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

        self.loaded_messages = deque(sorted(self.loaded_messages, key=lambda msg: msg["tick"]))

        logging.info(f"Load procedure finished. {len(self.loaded_messages)} event(s) loaded.")

    def build_events(self, progress_callback=lambda x, y: None, limitation=inf):
        for plugin in self.plugins:
            for dependency in plugin.__dependencies__:
                assert dependency in tuple(
                    map(type, self.plugins)), f"Dependency {dependency} of {plugin} is required, but not found."
            for conflict in plugin.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.plugins)), f"Conflict {conflict} of {plugin} is *PROHIBITED*, but found."
            plugin.init(self)

        self.built_tick_count = 0  # For plugins
        self.built_function.clear()

        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        self.loaded_tick_count = max(self.loaded_messages, key=lambda msg: msg["tick"])["tick"]  # For plugins

        for self.tick_index in range(-self.blank_ticks, self.loaded_tick_count + 1):
            self.build_axis_index = self.built_tick_count % self.wrap_length  # For plugins
            self.wrap_axis_index = self.built_tick_count // self.wrap_length  # For plugins
            self.is_first_tick = self.is_last_tick = False

            if self.tick_index == -self.blank_ticks:
                self.is_first_tick = True
            if self.tick_index == self.loaded_tick_count:
                self.is_last_tick = True

            if (self.built_tick_count + 1) % self.wrap_length == 0:
                self._set_command_block(  # Row to wrap
                    chain=0, auto=0, command=f"setblock ~{1 - self.wrap_length} ~-1 ~1 minecraft:redstone_block")
            else:
                self._set_command_block(  # Ordinary row
                    chain=0, auto=0, command="setblock ~1 ~-1 ~ minecraft:redstone_block")

            self._set_command_block(command="setblock ~ ~-2 ~ minecraft:air replace")  # Remove redstone block

            while (message := self.loaded_messages) and message[0]["tick"] == self.tick_index:
                self.tick_cache.append(self.loaded_messages.popleft())  # Deque object is used to improve performance

            message_count = 0  # Limitation here for this tick

            for message in self.tick_cache:
                if message_count > limitation:
                    break  # Limitation exceeds

                if message["type"] == "note_on":
                    self.set_tick_command(command=self.get_play_cmd(message))

                elif message["type"] == "note_off":
                    self.set_tick_command(command=self.get_stop_cmd(message))

                message_count += 1

            for plugin in self.plugins:  # Execute plugin
                plugin.exec(self)

            # Get ready for next tick
            self.built_tick_count += 1
            self.tick_cache.clear()
            self.y_index = 0

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
            y_shift = self.y_index
        if z_shift is None:
            z_shift = self.wrap_axis_index
        if command is None:
            return None

        for unsafe, alternative in self.STRING_UNSAFE.items():
            command = command.replace(unsafe, alternative)

        setblock_cmd = f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{"chain_" if chain else ""}command_block[facing={facing}]{{auto:{"true" if auto else "false"},Command:"{command}",LastOutput:false,TrackOutput:false}} replace'
        self.built_function.append(setblock_cmd)

        self.y_index += 1

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
    from gsmidi.frontends import SomaExtended
    from gsmidi.plugins import large_title, piano_roll, progress, viewport

    logging.basicConfig(level=logging.DEBUG)

    generator = Generator(r"D:\音乐\【完美佳作03】打上花火 - DAKAO × 米津玄师.mid", SomaExtended(), plugins=[
        piano_roll.PianoRoll(),
        progress.Progress(
            text="(。・∀・)ノ 进度条"
        ),
        viewport.Viewport(
            *viewport.Viewport.PRESET2
        ),
        large_title.LargeTitle({
            "text": "打上花火",
            "color": "red"
        }, {
            "text": "By kworker"
        }),
    ])
    generator.tick_rate_analysis()
    generator.long_note_analysis()
    generator.load_messages()
    generator.build_events()
    generator.write_datapack(r"D:\Minecraft\.minecraft\versions\1.14.4-forge-28.1.56\saves\MCDI")
