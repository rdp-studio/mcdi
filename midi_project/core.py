"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

from math import floor, ceil
from time import time

import mido

from command_types import *


class Generator(mido.MidiFile):
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
        self.plugins = list(plugins)
        self.middles = list(middles)

        self.loaded_messages = list()
        self.namespace = namespace
        self.built_function = Function(namespace, func)
        self.plug_functions = list()
        self.tempo = 5E5

        self.id = int(time())

    def tick_analysis(self, expected_len=None, tolerance=10, step=0.1, strict=True,
                      progress_callback=lambda x, y: None):
        if not expected_len:
            expected_len = self.length

        max_tick = 0
        logging.debug("Analysing maximum and minimum tick rate.")
        track_count = len(self.tracks)
        count = 0
        for _, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {_}: {track}.")
            accum = sum(map(lambda x: x.time, track))
            max_tick = max(max_tick, accum)
            count += 1
            progress_callback(count, track_count)
        max_allow = 1 / ((expected_len - tolerance) * 20 / max_tick)
        min_allow = 1 / ((expected_len + tolerance) * 20 / max_tick)
        logging.debug(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1
        best_tick_rate = 1 / (expected_len * 20 / max_tick)
        i = minimum = floor(min_allow) if strict else min_allow
        maximum = ceil(max_allow) if strict else max_allow
        estimated_count = (maximum - i) / step
        count = 0

        while i < maximum:
            logging.debug(f"Trying tick rate: {i} between {minimum} and {maximum}.")
            time_diff_sum = 0
            message_sum = 0
            for _, track in enumerate(self.tracks):
                time_accum = 0
                for message in track:
                    time = time_accum + message.time
                    diff = abs(round(raw := (time / i)) - raw)
                    time_diff_sum += diff
                    message_sum += 1
                    time_accum += message.time
            time_diff_sum /= message_sum
            logging.debug(f"Average round difference for tick rate {i}: {time_diff_sum}.")
            if time_diff_sum < min_time_diff:
                min_time_diff = time_diff_sum
                best_tick_rate = i
            i += step
            count += 1

            progress_callback(count, estimated_count)

        logging.info(f"The best tick rate found: {best_tick_rate}.")
        self.tick_rate = best_tick_rate

    def long_note_analysis(self, threshold=40, progress_callback=lambda x, y: None):
        sustain_notes = []
        logging.debug("Analysing long notes.")
        track_count = len(self.tracks)
        count = 0

        for i, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {i}: {track}...")
            time_accum = 0
            for message in track:
                time_accum += message.time
                if message.type == "note_on":
                    vars(message)["abs_time"] = time_accum
                    sustain_notes.append(message)
                elif message.type == "note_off":
                    off_notes = filter(
                        lambda x: x.channel == message.channel and x.note == message.note, sustain_notes
                    )
                    for off_note in off_notes:
                        length = (time_accum - off_note.abs_time) / self.tick_rate
                        sustain_notes.remove(off_note)
                        if length >= threshold:
                            vars(off_note)["long"] = True
                            vars(message)["long"] = True
            count += 1
            progress_callback(count, track_count)
            logging.debug(f"Analysed long notes in track {i}.")

    def half_tick_analysis(self, minimum=0.3, maximum=0.7, progress_callback=lambda x, y: None):
        sustain_notes = []
        logging.debug("Analysing half-tick notes.")
        track_count = len(self.tracks)
        count = 0

        for i, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {i}: {track}...")
            time_accum = 0
            for message in track:
                time_accum += message.time
                if message.type == "note_on":
                    tick_diff = 1 - ceil(t := (time_accum / self.tick_rate)) + t
                    if minimum < tick_diff < maximum:
                        vars(message)["half"] = True
                        vars(message)["shift"] = - (round(t) > t)
                        sustain_notes.append(message)
                elif message.type == "note_off":
                    off_notes = filter(
                        lambda x: x.channel == message.channel and x.note == message.note, sustain_notes
                    )
                    for off_note in off_notes:
                        vars(message)["half"] = True
                        vars(message)["shift"] = 1
                        sustain_notes.remove(off_note)
            count += 1
            progress_callback(count, track_count)
            logging.debug(f"Analysed half-tick notes in track {i}.")

    def load_events(self, pan_enabled=True, gvol_enabled=True, pitch_enabled=True,
                    pitch_factor=1, volume_factor=1.0, limitation=float("inf")):
        self.pan_enabled = pan_enabled
        self.gvol_enabled = gvol_enabled
        self.pitch_enabled = pitch_enabled
        self.pitch_factor = pitch_factor
        self.volume_factor = volume_factor
        self.loaded_messages.clear()

        for _, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {_}: {track}...")

            time_accum = 0
            program_set = dict()
            volume_set = dict()
            pan_set = dict()
            pitch_set = dict()

            count = 0

            for message in track:
                if count > limitation:
                    break

                if message.is_meta:
                    if message.type == "end_of_track":
                        break
                    elif message.type == "set_tempo":
                        self.tempo = message.tempo
                    elif message.type == "copyright":
                        logging.info(f"MIDI copyright information: {message.text}")
                    continue

                time = time_accum + message.time
                tick_time = round(time / self.tick_rate)

                if "note" in message.type:
                    program = 1  # Default
                    if message.channel == 9:
                        program = 0  # Force drum
                    elif message.channel in program_set.keys():
                        program = program_set[message.channel]["value"] + 1

                    if message.channel in volume_set.keys() and self.gvol_enabled:
                        volume = volume_set[message.channel]["value"] / 127
                    else:
                        volume = 1
                    volume_value = volume * message.velocity * self.volume_factor
                    if message.channel in pan_set.keys() and self.pan_enabled:
                        pan_value = pan_set[message.channel]["value"]
                    else:
                        pan_value = 64
                    if message.channel in pitch_set.keys() and self.pitch_enabled:
                        pitch_value = pitch_set[message.channel]["value"] * 9.1552734E-5 * self.pitch_factor
                    else:
                        pitch_value = 1

                    if hasattr(message, "long"):
                        long = True
                    else:
                        long = False

                    if hasattr(message, "half"):
                        half = True
                        tick_time += message.shift
                    else:
                        half = False

                    self.loaded_messages.append({
                        "type": message.type,
                        "ch": message.channel,
                        "prog": program,
                        "note": message.note,
                        "v": volume_value,
                        "tick": tick_time,
                        "pan": pan_value,
                        "pitch": pitch_value,
                        "half": half,
                        "long": long
                    })

                    count += 1
                elif "prog" in message.type:
                    time = time_accum + message.time
                    program_set[message.channel] = {"value": message.program, "time": tick_time}
                elif "control" in message.type:
                    time = time_accum + message.time
                    if message.control == 7:
                        volume_set[message.channel] = {"value": message.value, "time": tick_time}
                    elif message.control == 121:
                        if message.channel in volume_set.keys():
                            del volume_set[message.channel]
                    elif message.control == 10:
                        pan_set[message.channel] = {"value": message.value, "time": tick_time}
                    else:
                        pass
                elif "pitch" in message.type:
                    time = time_accum + message.time
                    pitch_set[message.channel] = {"value": message.pitch, "time": tick_time}
                else:
                    print(message)
                time_accum += message.time

                for plugin in self.middles:
                    plugin.exec(self)

        self.loaded_messages.sort(key=lambda n: n["tick"])
        logging.info("Load process finished.")

    def build_events(self, progress_callback=lambda x, y: None, limitation=511):
        for plugin in self.middles:
            if hasattr(plugin, "init"):
                plugin.init(self)
        for plugin in self.plugins:
            if hasattr(plugin, "init"):
                plugin.init(self)

        self.built_function.clear()

        self.build_count = 0
        self.y_index = 0
        self.tick_cache = list()
        self.tick_count = 0
        self.tick_sum = max(self.loaded_messages, key=lambda x: x["tick"])["tick"]

        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        self.end_tick = max(self.loaded_messages, key=lambda x: x["tick"])["tick"]
        for self.tick_count in range(-self.blank_ticks, self.end_tick + 1):
            self.build_index = self.build_count % self.wrap_length
            self.wrap_index = self.build_count // self.wrap_length

            if (self.build_count + 1) % self.wrap_length == 0:
                self._set_command_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                        chain=False, auto=False,
                                        command=self.get_front_shift_cmd(1 - self.wrap_length, -1, 1))
                self.y_index += 1
            else:
                self._set_command_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                        chain=False, auto=False,
                                        command=self.get_front_shift_cmd(1, -1, 0))
                self.y_index += 1

            self._set_command_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                    command=self.get_deactivate_cmd(0, -2, 0))
            self.y_index += 1

            while (m := self.loaded_messages) and m[0]["tick"] == self.tick_count:
                self.tick_cache.append(self.loaded_messages.pop(0))

            count = 0

            for message in self.tick_cache:
                if count > limitation:
                    break
                if message["type"] == "note_on":
                    if self._set_tick_command(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                              command=self.get_play_cmd(message)):
                        self.y_index += 1
                    count += 1
                elif message["type"] == "note_off":
                    if self._set_tick_command(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                              command=self.get_stop_cmd(message)):
                        self.y_index += 1
                    count += 1

            for plugin in self.plugins:
                plugin.exec(self)

            self.build_count += 1
            self.y_index = 0

            if self.tick_count % 100 == 0:
                logging.info(f"Built {self.tick_count} tick(s), {self.end_tick + 1} tick(s) in all.")
                progress_callback(self.tick_count, self.end_tick + 1)
            self.tick_cache.clear()

        logging.info("Build process finished.")
        logging.debug(f"Estimated duration: {self.tick_count / 20} second(s)。")

    def write_func(self, *args, **kwargs):
        logging.info(f"Writing {len(self.built_function)} command(s) built.")
        for i, function in enumerate(self.plug_functions):
            self.built_function.append(f"schedule function {function.id[0]}:{function.id[1]} {i + 1}")
        self.built_function.write(*args, **kwargs)
        for function in self.plug_functions:
            function.write(*args, **kwargs)
        logging.info("Write process finished.")

    def get_play_cmd(self, message):
        return self.frontend.get_play_cmd(**message)

    def get_stop_cmd(self, message):
        return self.frontend.get_stop_cmd(**message)

    @staticmethod
    def get_front_shift_cmd(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:redstone_block replace"

    @staticmethod
    def get_deactivate_cmd(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:air replace"

    def _set_tick_command(self, command=None, *args, **kwargs):
        if command is None:
            return None
        command = command.replace("\"", r"\"")
        return self._set_command_block(command=command, *args, **kwargs)

    def _set_command_block(self, x_shift, y_shift, z_shift, chain=True, auto=True, command=None, facing="up"):
        if command is None:
            return None
        type_def = "chain_" if chain else ""
        auto_def = "true" if auto else "false"
        self.built_function.append(
            f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{type_def}command_block[facing={facing}]{{auto:{auto_def},Command:"{command}",LastOutput: false,TrackOutput: false}} replace')
        return True


if __name__ == '__main__':
    from midi_project.plugins import *
    from midi_project.frontends import *

    MIDI_PATH = r"D:\音乐\Only My Railgun Original.mid"  # Where you save your midi file.

    GAME_DIR = r"D:\Minecraft\.minecraft\versions\fabric-loader-0.8.2+build.194-1.14.4"  # Your game directory
    WORLD_NAME = r"_TEST"  # Your world name

    TICK_RATE = 60  # The higher, the faster
    EXPECTED_LEN = 0  # Overrides the tick rate, set to -1 to disable, set to 0 to automatic
    TOLERANCE = 3  # Works with expected length, set to 0 for fixed
    STEP = 0.05  # Works with expected length, DO NOT set to 0!!
    LONG_NOTE_LEVEL = 30  # Set to 0 to disable

    PAN_ENABLED = True  # Whether you want to use the pan or not
    GLOBAL_VOLUME_ENABLED = True  # Whether you want to use the global volume or not
    PITCH_ENABLED = True  # Whether you want to use the pitch value or not
    PITCH_FACTOR = 1  # How much do you want the pitch value to be
    VOLUME_FACTOR = 1  # 1 as default, the bigger, the louder

    FRONT_END = Soma()

    MIDDLEWARES = [

    ]

    PLUGINS = [
        PianoRoll()
    ]

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    gen = Generator(MIDI_PATH, tick_rate=TICK_RATE,
                    plugins=PLUGINS, middles=MIDDLEWARES, frontend=FRONT_END)
    if 0 <= EXPECTED_LEN:
        gen.tick_analysis(EXPECTED_LEN, TOLERANCE, STEP)
    if 0 < LONG_NOTE_LEVEL:
        gen.long_note_analysis(LONG_NOTE_LEVEL)
    # gen.half_tick_analysis()
    gen.load_events(pan_enabled=PAN_ENABLED, gvol_enabled=GLOBAL_VOLUME_ENABLED, pitch_enabled=PITCH_ENABLED,
                    pitch_factor=PITCH_FACTOR, volume_factor=VOLUME_FACTOR)
    gen.build_events()
    gen.write_func(os.path.join(GAME_DIR, "saves", WORLD_NAME))
