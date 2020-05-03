"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
import os
from math import ceil, floor

import mido


class Generator(mido.MidiFile):
    def __init__(self, fp, frontend, wrap_length=128, wrap_axis="x", tick_time=50, pan_enabled=True, gvol_enabled=True,
                 pitch_enabled=True, pitch_factor=2.5E-4, volume_factor=1.0, plugins=None, middles=None, blank_ticks=0):
        if plugins is None:
            plugins = []
        if middles is None:
            middles = []
        logging.debug("Initializing generator...")
        super().__init__(fp)
        self.wrap_length = wrap_length
        self.wrap_axis = wrap_axis
        self.tick_time = tick_time
        self.pan_enabled = pan_enabled
        self.gvol_enabled = gvol_enabled
        self.pitch_enabled = pitch_enabled
        self.pitch_factor = pitch_factor
        self.volume_factor = volume_factor
        self.plugins = list(plugins)
        self.middles = list(middles)

        self.loaded_messages = list()
        self.built_commands = list()
        self.tempo = 5E5
        self.blank_ticks = blank_ticks
        self.frontend = frontend
        for plugin in self.middles:
            if hasattr(plugin, "init"):
                plugin.init(self)
        for plugin in self.plugins:
            if hasattr(plugin, "init"):
                plugin.init(self)

    def tick_analysis(self, expected_len=None, tolerance=10, step=0.1, strict=False):
        if not expected_len:
            expected_len = self.length

        max_tick = 0
        logging.debug("Calculating maximum and minimum tick rate.")
        for _, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {_}: {track}.")
            accum = sum(map(lambda x: x.time, track))
            max_tick = max(max_tick, accum)
        max_allow = 1 / ((expected_len - tolerance) * 20 / max_tick)
        min_allow = 1 / ((expected_len + tolerance) * 20 / max_tick)
        logging.info(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1
        best_tick_rate = 1 / (expected_len * 20 / max_tick)
        i = floor(min_allow) if strict else min_allow

        while i < (ceil(max_allow) if strict else max_allow):
            logging.debug(f"Trying tick rate: {i} within the limitation.")
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
            logging.debug(f"Average round difference: {time_diff_sum}.")
            if time_diff_sum < min_time_diff:
                min_time_diff = time_diff_sum
                best_tick_rate = i
            i += step

        logging.info(f"Best tick rate found: {best_tick_rate}.")
        self.tick_time = best_tick_rate

    def long_note_analysis(self, threshold=40):
        sustain_notes = []
        logging.debug("Analysing long notes.")
        for i, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {i}: {track}...")
            time_accum = 0
            for message in track:
                time_accum += message.time
                if message.type == "note_on":
                    vars(message)["abs_time"] = time_accum
                    sustain_notes.append(message)
                elif message.type == "note_off":
                    off_notes = filter(lambda x: x.channel == message.channel and x.note == message.note, sustain_notes)
                    for off_note in off_notes:
                        vars(off_note)["length"] = time_accum - off_note.abs_time
                        if off_note in sustain_notes:
                            sustain_notes.remove(off_note)
                        if off_note.length >= threshold:
                            vars(off_note)["L"] = True
                            vars(message)["L"] = True
            logging.debug(f"Analysed long notes in track {i}.")

    def load_events(self):
        self.loaded_messages.clear()

        for _, track in enumerate(self.tracks):
            logging.debug(f"Reading events from track {_}: {track}...")

            time_accum = 0
            programs = dict()
            volumes = dict()
            pans = dict()
            pitchs = dict()

            for message in track:
                if message.is_meta:
                    if message.type == "end_of_track":
                        break
                    elif message.type == "set_tempo":
                        self.tempo = message.tempo
                    elif message.type == "copyright":
                        logging.info(f"MIDI copyright information: {message.text}")
                    continue

                time = time_accum + message.time
                tick_time = round(time / self.tick_time)

                if "note" in message.type:
                    if message.channel == 9:
                        program = 0  # Force drum
                    elif message.channel in programs.keys():
                        program = programs[message.channel]["value"]
                    else:
                        program = 1  # Default

                    if message.channel in volumes.keys() and self.gvol_enabled:
                        volume = volumes[message.channel]["value"]
                    else:
                        volume = 1
                    volume_value = volume * message.velocity * self.volume_factor
                    if message.channel in pans.keys() and self.pan_enabled:
                        pan_value = pans[message.channel]["value"]
                    else:
                        pan_value = 64
                    if message.channel in pitchs.keys() and self.pitch_enabled:
                        pitch_value = 1 + pitchs[message.channel]["value"] * self.pitch_factor
                    else:
                        pitch_value = 1

                    if hasattr(message, "L"):
                        long = True
                    else:
                        long = False

                    self.loaded_messages.append(
                        {"type": message.type, "ch": message.channel, "prog": program, "note": message.note,
                         "v": volume_value, "tick": tick_time, "pan": pan_value, "pitch": pitch_value, "long": long}
                    )
                elif "prog" in message.type:
                    time = time_accum + message.time
                    programs[message.channel] = {"value": message.program + 1, "time": tick_time}
                elif "control" in message.type:
                    time = time_accum + message.time
                    if message.control == 7:
                        volumes[message.channel] = {"value": message.value / 127, "time": tick_time}
                    elif message.control == 121:
                        if message.channel in volumes.keys():
                            del volumes[message.channel]
                    elif message.control == 10:
                        pans[message.channel] = {"value": message.value, "time": tick_time}
                elif "pitch" in message.type:
                    time = time_accum + message.time
                    pitchs[message.channel] = {"value": message.pitch, "time": tick_time}
                time_accum += message.time

                for plugin in self.middles:
                    plugin.exec(self)

        self.loaded_messages.sort(key=lambda n: n["tick"])
        logging.info("Load process finished.")

    def build_events(self):
        self.built_commands.clear()

        self.build_count = 0
        self.y_index = 0
        self.tick_cache = list()
        self.tick = 0

        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        self.end_tick = max(self.loaded_messages, key=lambda x: x["tick"])["tick"]
        for self.tick in range(-self.blank_ticks, self.end_tick + 1):
            self.build_index = self.build_count % self.wrap_length
            self.wrap_index = self.build_count // self.wrap_length

            if (self.build_count + 1) % self.wrap_length == 0:
                self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index, chain=False,
                                   auto=False, command=self.set_redstone_block_cmd(1 - self.wrap_length, -1, 1))
                self.y_index += 1
            else:
                self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index, chain=False,
                                   auto=False, command=self.set_redstone_block_cmd(1, -1, 0))
                self.y_index += 1

            self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                               command=self.set_air_block_cmd(0, -2, 0))
            self.y_index += 1

            while (m := self.loaded_messages) and m[0]["tick"] == self.tick:
                self.tick_cache.append(self.loaded_messages.pop(0))

            for message in self.tick_cache:
                if message["type"] == "note_on":
                    if self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                       command=self.play_cmd(message)):
                        self.y_index += 1
                elif message["type"] == "note_off":
                    if self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                       command=self.stop_cmd(message)):
                        self.y_index += 1

            for plugin in self.plugins:
                plugin.exec(self)

            self.build_count += 1
            self.y_index = 0

            if self.tick % 5E2 == 0:
                logging.info(f"Built {self.tick} tick(s), {self.end_tick + 1} tick(s) in all.")
            self.tick_cache.clear()

        logging.info("Build process finished.")
        logging.debug(f"Estimated duration: {self.tick / 20} second(s)。")

    def write_func(self, wp, namespace="mcdi", func="music"):
        logging.info(f"Writing {(length := len(self.built_commands))} command(s) built.")
        if length >= 65536:
            logging.warning("Notice: please try this command as your music function is longer than 65536 line(s).")
            logging.warning("Try this: /gamerule maxCommandChainLength %d" % (length + 1))  # Too long

        if os.path.exists(wp):
            os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\%s\functions" % namespace), exist_ok=True)
        else:
            raise FileNotFoundError("World path or Minecraft path does not exist!")
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\%s\functions\%s.mcfunction" % (namespace, func)), "w") as file:
            file.writelines(self.built_commands)
        logging.info("Write process finished.")
        logging.debug("To run the music function: '/reload'")
        logging.debug(f"Then: '/function {namespace}:{func}'")

    def play_cmd(self, message):
        return self.frontend.play_cmd(**message)

    def stop_cmd(self, message):
        return self.frontend.stop_cmd(**message)

    @staticmethod
    def set_redstone_block_cmd(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:redstone_block replace"

    @staticmethod
    def set_air_block_cmd(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:air replace"

    def set_cmd_block(self, x_shift, y_shift, z_shift, chain=True, repeat=False, auto=True, command=None, facing="up"):
        if command is None:
            return None
        type_def = ("chain_" if chain else "") or ("repeat_" if repeat else "")
        auto_def = "true" if auto else "false"
        self.built_commands.append(
            f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{type_def}command_block[facing={facing}]{{auto: '
            f'{auto_def}, Command: "{command}", LastOutput: false, TrackOutput: false}} replace\n'
        )
        return True


if __name__ == '__main__':
    from midi_project.plugins import *
    from midi_project.frontends import *

    MIDI_PATH = r"D:\midi\only_my_railgun_guitar.mid"  # Where you save your midi file.

    GAME_DIR = r"D:\Minecraft\.minecraft\versions\fabric-loader-0.8.2+build.194-1.14.4"  # Your game directory
    WORLD_NAME = r"Tester"  # Your world name

    TICK_RATE = 60  # The higher, the faster
    EXPECTED_LEN = 0  # Overrides the tick rate, set to -1 to disable, set to 0 to automatic
    TOLERANCE = 0  # Works with expected length, set to 0 for fixed
    STEP = 0.05  # Works with expected length
    LONG_NOTE_LEVEL = 40  # Set to 0 to disable

    PAN_ENABLED = True  # Whether you want to use the pan or not
    GLOBAL_VOLUME_ENABLED = True  # Whether you want to use the global volume or not
    PITCH_ENABLED = True  # Whether you want to use the pitch value or not
    PITCH_FACTOR = 0.05  # How much do you want the pitch value to be
    VOLUME_FACTOR = 1.5  # 1 as default, the bigger, the louder

    FRONT_END = Soma()

    MIDDLEWARES = [

    ]

    PLUGINS = [
        PianoFall()
    ]

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    gen = Generator(MIDI_PATH, tick_time=TICK_RATE, pan_enabled=PAN_ENABLED, gvol_enabled=GLOBAL_VOLUME_ENABLED,
                    pitch_enabled=PITCH_ENABLED, pitch_factor=PITCH_FACTOR, volume_factor=VOLUME_FACTOR,
                    plugins=PLUGINS, middles=MIDDLEWARES, frontend=FRONT_END)
    if 0 <= EXPECTED_LEN:
        gen.tick_analysis(EXPECTED_LEN, TOLERANCE, STEP)
    if 0 < LONG_NOTE_LEVEL:
        gen.long_note_analysis(LONG_NOTE_LEVEL)
    gen.load_events()
    gen.build_events()
    gen.write_func(os.path.join(GAME_DIR, "saves", WORLD_NAME))
