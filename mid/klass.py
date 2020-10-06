"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
import uuid
from abc import abstractmethod
from collections import deque
from math import floor, ceil

from mido import MidiFile, tick2second, MidiTrack
from mido.midifiles.tracks import fix_end_of_track

from base.command_types import *
from base.minecraft_types import *


def float_range(start, stop, step):
    while start <= stop if step > 0 else start >= stop:
        yield start
        start += step


def rand_uuid():
    return str(uuid.uuid4()).replace("-", "")


def rand_func(namespace):
    return Function(
        namespace, rand_uuid()
    )


def fast_copy(message, **overrides):  # Insecure!!
    msg = message.__class__.__new__(message.__class__)
    vars(msg).update(vars(message))
    vars(msg).update(overrides.copy())
    return msg


def _to_abstime(messages):
    now = 0
    for msg in messages:
        now += msg.time
        yield fast_copy(msg, time=now)


def _to_reltime(messages):
    now = 0
    for msg in messages:
        delta = msg.time - now
        yield fast_copy(msg, time=delta)
        now = msg.time


def fast_merge(tracks):
    messages = []
    for track in tracks:
        messages.extend(_to_abstime(track))

    messages.sort(key=lambda msg: msg.time)

    return MidiTrack(fix_end_of_track(_to_reltime(messages)))


class BaseGenerator(MidiFile):
    STRING_UNSAFE = {
        "\n": r'\n',
        "\\": r"\\",
        r'"': r'\"',
    }

    def __init__(self, fp, namespace="mcdi", identifier="music", **kwargs):
        logging.debug("Initializing. Reading MIDI data.")

        super(BaseGenerator, self).__init__(fp)

        self.blank_ticks = 0
        self.tick_rate = 20
        self.tick_scale = 1
        self.namespace = namespace
        # Build variables
        self.tick_cache = list()
        self.loaded_tick_count = 0
        # Function stuffs
        self.loaded_messages = deque()
        self.built_function = Function(
            namespace, identifier
        )
        self.gentime_functions = list()
        self.runtime_functions = list()
        # Tick packages
        self.single_tick_limit = 128

        logging.debug("Preloading tracks.")
        self._merged_track = fast_merge(
            self.tracks
        )  # Preload tracks for speed
        self._preloaded = list(self._preload())
        # Preload messages for speed
        vars(self)["length"] = self.length

        for key, value in kwargs.items():
            assert key in vars(self).keys(), f"'{self.__class__.__name__}' object has no attribute '{key}'"
            vars(self)[key] = value

    def write_datapack(self, *args, **kwargs):
        # Reduces lag
        self.built_function.append(f"gamerule commandBlockOutput false")
        self.built_function.insert(
            0, f"gamerule maxCommandChainLength 2147483647"
        )

        logging.info(f"Writing {len(self.built_function)} command(s) built.")

        for i, function in enumerate(self.gentime_functions):  # These runs with the build func.
            self.built_function.append(f"function {function.namespace}:{function.identifier}")

        self.built_function.to_pack(*args, **kwargs)  # Save to datapack

        for function in self.gentime_functions + self.runtime_functions:
            function.to_pack(*args, **kwargs)  # Save these to datapack

        logging.info("Write procedure finished. Now enjoy your music!")

    def _preload(self):  # Insecure!!
        tempo = 5e5

        for msg in self._merged_track:
            yield fast_copy(
                msg, time=tick2second(msg.time, self.ticks_per_beat, tempo) if msg.time > 0 else 0
            )

            if msg.type == 'set_tempo':
                tempo = msg.tempo

    def __iter__(self):  # Insecure!!
        return iter(self._preloaded)


class BaseCbGenerator(BaseGenerator):
    def __init__(self, plugins=None, *args, **kwargs):
        if plugins is None:
            self.plugins = []
        else:
            self.plugins = list(plugins)

        self.wrap_length = 128
        # Build variables
        self.tick_index = 0
        # Plugin stuffs
        self.built_tick_count = 0
        self.y_axis_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.wrap_state = False
        self.is_first_tick = False
        self.is_last_tick = False

        # Tick package toggle
        self._use_function_array = False  # * Experimental *
        self._auto_function_array = False  # * Experimental *

        super(BaseCbGenerator, self).__init__(*args, **kwargs)

        if self._use_function_array:
            self._auto_function_array = False
        if self._auto_function_array:
            self._use_function_array = False

        # Tick package manager
        self.current_tick_pkg = rand_func(self.namespace)
        # Scheduler
        self.schedules = {}

    def auto_tick_rate(self, duration=None, tolerance=5, step=.01, base=20, strict=False):
        if not duration:  # Calculate the length myself
            duration = self.length

        logging.info("Try finding the best tick rate.")

        max_allow = base + base * (tolerance / duration)  # Max acceptable tick rate
        min_allow = base - base * (tolerance / duration)  # Min acceptable tick rate
        logging.info(f"Maximum and minimum tick rate: {max_allow}, {min_allow}.")

        min_time_diff = 1  # No bigger than 1 possible
        best_tick_rate = base  # The no-choice fallback
        maximum = floor(max_allow) if strict else max_allow  # Rounded max acceptable tick rate
        minimum = ceil(min_allow) if strict else min_allow  # Rounded min acceptable tick rate

        for i in float_range(minimum, maximum, step):
            timestamp = message_count = round_diff_sum = 0

            for message in self:
                round_diff_sum += abs(round(raw := (timestamp * i)) - raw)
                timestamp += message.time
                message_count += 1
            round_diff_sum /= message_count

            if round_diff_sum < min_time_diff:
                min_time_diff = round_diff_sum
                best_tick_rate = float(i)

            logging.info(f"Tick rate = {i}, round difference = {round_diff_sum}.")

        self.tick_rate = best_tick_rate

        logging.info(f"The best tick rate found: {best_tick_rate}.")

    def _add_tick_package(self):
        self.runtime_functions.append(pkg := self.current_tick_pkg)
        self._set_command_block(
            command=f"function {self.namespace}:{pkg.identifier}"
        )
        self.current_tick_pkg = rand_func(self.namespace)

    def add_tick_command(self, command=None, *args, **kwargs):
        if self._use_function_array:  # Use funcs to build music
            return self.current_tick_pkg.append(command=command)
        self._set_command_block(command=command, *args, **kwargs)

    def _set_command_block(self, x_shift=None, y_shift=None, z_shift=None, chain=1, auto=1, command=None, facing="up"):
        if x_shift is None:
            x_shift = self.build_axis_index
        if y_shift is None:
            y_shift = self.y_axis_index
        if z_shift is None:
            z_shift = self.wrap_axis_index
        if command is None:
            return None

        for unsafe, alternative in self.STRING_UNSAFE.items():
            command = str(command).replace(unsafe, alternative)

        self.built_function.append(
            f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{"chain_" if chain else ""}command_block[facing='
            f'{facing}]{{auto:{"true" if auto else "false"},Command:"{command}",LastOutput:false,TrackOutput:false}}'
        )

        self.y_axis_index += 1

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

    @property
    def auto_function_array(self):
        return self._auto_function_array

    @auto_function_array.setter
    def auto_function_array(self, value):
        if value:
            warnings.warn(RuntimeWarning(
                "Function array is a unstable feature and you may *NOT* commit a issue for that."
            ))
        self._auto_function_array = value

    def _reset_build_status(self):
        self.built_function.clear()

        # Clear built items
        self.tick_cache.clear()
        self.built_tick_count = 0

        self.tick_index = 0
        self.y_axis_index = 0
        self.build_axis_index = 0
        self.wrap_axis_index = 0
        self.is_first_tick = self.is_last_tick = False

    def _init_plugin_status(self):
        for plugin in self.plugins:
            for dependency in plugin.__dependencies__:
                assert dependency in tuple(
                    map(type, self.plugins)), f"Dependency {dependency} of {plugin} is required, but not found."
            plugin.dependency_connect(filter(lambda x: type(x) in plugin.__dependencies__, self.plugins))
            for conflict in plugin.__conflicts__:
                assert conflict not in tuple(
                    map(type, self.plugins)), f"Conflict {conflict} of {plugin} is strictly forbidden, but found."
            plugin.init(self)

    def _update_build_status(self):
        self.build_axis_index = self.built_tick_count % self.wrap_length  # For plugins
        self.wrap_axis_index = self.built_tick_count // self.wrap_length  # For plugins
        self.wrap_state = (self.built_tick_count + 1) % self.wrap_length == 0
        self.is_first_tick = self.is_last_tick = False

        if self.tick_index == -self.blank_ticks:
            self.is_first_tick = True
        if self.tick_index == self.loaded_tick_count:
            self.is_last_tick = True

        if self.wrap_state:
            self._set_command_block(  # Row to wrap
                chain=0, auto=0, command=f"setblock ~{1 - self.wrap_length} ~-1 ~1 minecraft:redstone_block")
        else:
            self._set_command_block(  # Ordinary row
                chain=0, auto=0, command="setblock ~1 ~-1 ~ minecraft:redstone_block")

        self._set_command_block(command="setblock ~ ~-2 ~ minecraft:air replace")  # Remove redstone block

    def _update_farray_status(self):
        if self.auto_function_array:
            if len(self.tick_cache) > 127:
                self.current_tick_pkg = rand_func(self.namespace)
                self._use_function_array = True
            else:
                self._use_function_array = False

    def _execute_schedules(self):
        if self.tick_index in self.schedules.keys():
            for i, x, y, z in self.schedules[self.tick_index]:
                x, y, z = x(self) if x else 0, y(self) if y else 0, z(self) if z else 0
                self.add_tick_command(command=f"execute positioned ~{x} ~{y} ~{z} run {i}")
            del self.schedules[self.tick_index]

    def _reload_build_status(self):
        if self._use_function_array:
            self._add_tick_package()

        # Get ready for next tick
        self.built_tick_count += 1
        self.tick_cache.clear()
        self.y_axis_index = 0

    # Plugin APIs

    def schedule(self, dt, command, x=None, y=None, z=None):
        if self.tick_index + dt not in self.schedules.keys():
            self.schedules[self.tick_index + dt] = []

        self.schedules[self.tick_index + dt].append((command, x, y, z))

    @abstractmethod
    def on_notes(self, ch=None):
        pass

    @abstractmethod
    def off_notes(self, ch=None):
        pass

    @abstractmethod
    def current_on_notes(self, ch=None):
        pass

    @abstractmethod
    def current_off_notes(self, ch=None):
        pass

    @abstractmethod
    def future_on_notes(self, tick, ch=None):
        pass

    @abstractmethod
    def future_off_notes(self, tick, ch=None):
        pass
