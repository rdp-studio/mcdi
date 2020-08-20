import logging
import zipfile
from collections import deque
from random import randint

from base.minecraft_types import *


class Generator(object):
    def __init__(self, fp, pack_name, namespace="mcdi", identifier="vocal"):
        logging.debug("Initializing. Reading VPR data.")

        with zipfile.ZipFile(fp, mode="r", compresslevel=None) as file:
            file.extract("Project/sequence.json")
        with open("Project/sequence.json", "r", encoding="utf8") as file:
            self.raw_sequence_json = json.load(file)

        self.pack_name = pack_name
        self.namespace = namespace
        self.wrap_length = 128
        self.blank_ticks = 0

        self.tick_cache = list()
        self.build_count = 0
        self.build_index = 0
        self.tick_sum = 0
        self.tick_index = 0
        self.wrap_index = 0
        self.y_index = 0

        self.loaded_messages = deque()
        self.built_function = Function(
            namespace, func
        )
        self.numer = 4
        self.denom = 4
        self.tempo = 120

        self.id = randint(0, 2 ** 31 - 1)

    def load_messages(self, volume_factor=1.75, mapping=None, language="japanese", limitation=float("inf")):
        message_count = 0  # Limitation here for the whole VPR file

        self.tempo = self.raw_sequence_json["masterTrack"]["tempo"]["events"][0]["value"] / 100
        self.numer = self.raw_sequence_json["masterTrack"]["timeSig"]["events"][0]["numer"]
        self.denom = self.raw_sequence_json["masterTrack"]["timeSig"]["events"][0]["denom"]

        for i, track in enumerate(self.raw_sequence_json["tracks"]):
            logging.debug(f"Reading events from track {i}: {track['name']}...")

            for part in track["parts"]:
                if "notes" not in part.keys():
                    continue  # An audio track

                last_lyric = None  # For "-" note continue

                for note in part["notes"]:
                    if message_count > limitation:
                        break  # Limitation exceeds

                    if mapping and note["lyric"] in mapping.keys():
                        note["lyric"] = mapping[note["lyric"]]  # Replace the lyric
                    if note["lyric"] in ("-", "ー") and last_lyric:  # Continue the note
                        if language == "japanese":  # Japanese fix
                            if len(last_lyric) == 1:  # A E I O U
                                note["lyric"] = last_lyric
                            else:  # ka, ku, kya, kyu, shi, chi, ...
                                note["lyric"] = last_lyric[-1]
                        note["c"] = True  # Mark as a continue note

                    real_note_pos = note["pos"] + part["pos"]
                    on_in_second = real_note_pos / 1920 * (60 / self.tempo) * self.denom
                    duration = note["duration"] / 1920 * (60 / self.tempo) * self.denom
                    off_in_second = on_in_second + duration
                    on_tick, off_tick = round(on_in_second * 20), round(off_in_second * 20)
                    self.loaded_messages.append({
                        "type": "note_on",
                        "lrc": note["lyric"],
                        "note": note["number"],
                        "v": note["velocity"] * volume_factor,
                        "tick": on_tick,
                        "c": "c" in note.keys()
                    })
                    self.loaded_messages.append({
                        "type": "note_off",
                        "lrc": note["lyric"],
                        "note": note["number"],
                        "v": note["velocity"] * volume_factor,
                        "tick": off_tick,
                        "c": "c" in note.keys()
                    })

                    message_count += 1
                    last_lyric = note["lyric"]

        self.loaded_messages = deque(sorted(self.loaded_messages, key=lambda m: m["tick"]))

        logging.info(f"Load process finished. {len(self.loaded_messages)} event(s) loaded.")

    def build_events(self, progress_callback=lambda x, y: None, limitation=511):
        self.built_function.clear()

        logging.debug(f'Building {len(self.loaded_messages)} event(s) loaded.')

        self.tick_sum = max(self.loaded_messages, key=lambda x: x["tick"])["tick"]
        for self.tick_index in range(-self.blank_ticks, self.tick_sum + 1):
            self.build_index = self.build_count % self.wrap_length  # For plugins
            self.wrap_index = self.build_count // self.wrap_length  # For plugins

            if (self.build_count + 1) % self.wrap_length == 0:
                self._set_command_block(  # Row to wrap
                    chain=0, auto=0, command=f"setblock ~{1 - self.wrap_length} ~-1 ~1 minecraft:redstone_block")
                self.y_index += 1
            else:
                self._set_command_block(  # Ordinary row
                    chain=0, auto=0, command="setblock ~1 ~-1 ~ minecraft:redstone_block")
                self.y_index += 1

            self._set_command_block(command="setblock ~ ~-2 ~ minecraft:air replace")  # Remove redstone block
            self.y_index += 1

            while (m := self.loaded_messages) and m[0]["tick"] == self.tick_index:  # While still message for this tick
                self.tick_cache.append(self.loaded_messages.popleft())  # Deque object is used for performance

            message_count = 0  # Limitation here for this tick

            for message in self.tick_cache:
                if message_count > limitation:
                    break  # Limitation exceeds

                if message["type"] == "note_on":
                    if self._set_tick_command(command=self.get_play_cmd(**message)):
                        self.y_index += 1

                elif message["type"] == "note_off":
                    if self._set_tick_command(command=self.get_stop_cmd(**message)):
                        self.y_index += 1

                message_count += 1

            # Get ready for next row
            self.build_count += 1
            self.tick_cache.clear()
            self.y_index = 0

            if self.tick_index % 100 == 0:  # Show progress
                logging.info(f"Built {self.tick_index} tick(s), {self.tick_sum + 1} tick(s) in all.")
                progress_callback(self.tick_index, self.tick_sum + 1)  # For GUI

        logging.info(f"Build process finished. {len(self.built_function)} command(s) built.")

    def get_play_cmd(self, lrc, note, v, **kwargs):
        return f"execute as @a at @s run playsound {self.pack_name}.{lrc}.{note} voice @s ~ ~ ~ {v / 127}"

    def get_stop_cmd(self, lrc, note, **kwargs):
        return f"execute as @a at @s run stopsound @s voice {self.pack_name}.{lrc}.{note}"

    def _set_tick_command(self, command=None, *args, **kwargs):
        return self._set_command_block(command=command.replace("\"", r"\""), *args, **kwargs)

    def _set_command_block(self, x_shift=None, y_shift=None, z_shift=None, chain=1, auto=1, command=None, facing="up"):
        if x_shift is None:
            x_shift = self.build_index
        if y_shift is None:
            y_shift = self.y_index
        if z_shift is None:
            z_shift = self.wrap_index
        if command is None:
            return None
        type_def = "chain_" if chain else ""
        auto_def = "true" if auto else "false"
        setblock_cmd = f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{type_def}command_block[facing={facing}]{{auto:{auto_def},Command:"{command}",LastOutput:false,TrackOutput:false}} replace'
        self.built_function.append(setblock_cmd)
        return True

    def write_datapack(self, *args, **kwargs):
        # Reduces lag
        self.built_function.append(f"gamerule commandBlockOutput false")
        self.built_function.append(f"gamerule sendCommandFeedback false")

        logging.info(f"Writing {len(self.built_function)} command(s) built.")

        self.built_function.to_pack(*args, **kwargs)  # Save to datapack

        logging.info("Write process finished. Now enjoy your music!")