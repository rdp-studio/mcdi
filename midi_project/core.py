"""
Requirements:
Python 3.8.x
- Package: mido
Minecraft 1.15.x
"""

import logging
import os

import mido

MIDI_DIR = r"D:\桌面\Revenge.mid"  # Where you save your midi file.

GAME_DIR = r"D:\Minecraft\.minecraft\versions\1.15.2"  # Your game directory
WORLD_DIR = r"Test"  # Your world name
DATA_DIR = os.path.join(GAME_DIR, "saves", WORLD_DIR)  # NEVER CHANGE THIS

TICK_RATE = 76.8  # The higher, the faster

DRUM_ENABLED = True  # Whether you want to use the drum or not
PAN_ENABLED = True  # Whether you want to use the pan value or not
GLOBAL_VOLUME_ENABLED = True  # Whether you want to use the global volume or not
PITCH_ENABLED = False  # Whether you want to use the pitch value or not
PITCH_FACTOR = 0.00025  # How much do you want the pitch value to be
VOLUME_FACTOR = 1.5  # 1 as default, the bigger, the louder

MIDDLEWARES = [

]

PLUGINS = [

]


class Generator(mido.MidiFile):
    def __init__(self, fp, wrap_length=64, wrap_axis="x", tick_time=50, drum_enabled=False, pan_enabled=True,
                 gvol_enabled=True, pitch_enabled=True, pitch_factor=2.5E-4, volume_factor=1, plugins=None,
                 middles=None):
        if plugins is None:
            plugins = []
        if middles is None:
            middles = []
        logging.info("正在初始化生成器……")
        super().__init__(fp)
        self.wrap_length = wrap_length
        self.wrap_axis = wrap_axis
        self.tick_time = tick_time
        self.drum_enabled = drum_enabled
        self.pan_enabled = pan_enabled
        self.gvol_enabled = gvol_enabled
        self.pitch_enabled = pitch_enabled
        self.pitch_factor = pitch_factor
        self.volume_factor = volume_factor
        self.plugins = list(plugins)
        self.middles = list(middles)

        self.parsed_msgs = list()
        self.built_cmds = list()
        self.tempo = 5E5

        if self.plugins:
            logging.info("正在载入插件……")
        for i, cfg in enumerate(self.plugins):
            plg = cfg["package"]
            if not hasattr(plg, "MainObject"):
                logging.warning("已丢弃插件：%s，因为其不是一个合格的MCDI插件。" % plg.__file__)
                self.plugins.remove(plg)
                continue
            logging.info("已装载插件：%s。" % plg.__file__)
            if hasattr(plg, "__author__"):
                logging.info("- 此插件的作者是：%s" % plg.__author__)
            if hasattr(plg, "__doc__"):
                logging.info("- 此插件的自述：%s" % plg.__doc__)
            self.plugins[i] = plg.MainObject(*cfg["args"], **cfg["kwargs"])
        if self.middles:
            logging.info("正在载入中间件……")
        for i, cfg in enumerate(self.middles):
            plg = cfg["package"]
            if not hasattr(plg, "MainObject"):
                logging.warning("已丢弃中间件：%s，因为其不是一个合格的MCDI中间件。" % plg.__file__)
                self.middles.remove(plg)
                continue
            logging.info("已中间件插件：%s。" % plg.__file__)
            if hasattr(plg, "__author__"):
                logging.info("- 此中间件的作者是：%s" % plg.__author__)
            if hasattr(plg, "__doc__"):
                logging.info("- 此中间件的自述：%s" % plg.__doc__)
            self.middles[i] = plg.MainObject(*cfg["args"], **cfg["kwargs"])

    def parse_tracks(self):
        self.parsed_msgs.clear()
        for _, track in enumerate(self.tracks):
            logging.info("正在读取轨道 %d：%s 中的事件。" % (_, track))

            time_accum = 0
            time_diff_sum = 0
            programs = dict()
            volumes = dict()
            pans = dict()
            pitchs = dict()

            for msg in track:
                if msg.is_meta:
                    if msg.type == "end_of_track":
                        break
                    if msg.type == "set_tempo":
                        self.tempo = msg.tempo
                    continue
                time = time_accum + msg.time
                tick_time = round(raw := (time / self.tick_time))
                time_diff_sum += abs(raw - tick_time)
                if "note" in msg.type:
                    if msg.channel == 10:
                        program = 0  # Force drum
                    elif msg.channel in programs.keys():
                        program = programs[msg.channel]["value"]  # Can be set
                        if (not self.drum_enabled) and (program == 0):
                            program = 1
                    else:
                        program = 1  # Default
                    volume_value = (volumes[msg.channel]["value"] if msg.channel in volumes.keys() and self.gvol_enabled
                                    else 1) * msg.velocity * self.volume_factor
                    pan_value = pans[msg.channel]["value"] if msg.channel in pans.keys() and self.pan_enabled else 64
                    pitch_value = 1 + (pitchs[msg.channel]["value"] * self.pitch_factor if msg.channel in pitchs.keys()
                                                                                           and self.pitch_enabled else 0)
                    self.parsed_msgs.append({
                        "type": msg.type,
                        "ch": msg.channel,
                        "prog": program,
                        "note": msg.note,
                        "v": volume_value,
                        "tick": tick_time,
                        "pan": pan_value,
                        "pitch": pitch_value,
                    })
                elif "prog" in msg.type:
                    time = time_accum + msg.time
                    programs[msg.channel] = {"value": msg.program, "time": tick_time}
                elif "control" in msg.type:
                    time = time_accum + msg.time
                    if msg.control == 7:
                        volumes[msg.channel] = {"value": msg.value / 127, "time": tick_time}
                    elif msg.control == 121:
                        if msg.channel in volumes.keys():
                            del volumes[msg.channel]
                    elif msg.control == 10:
                        pans[msg.channel] = {"value": msg.value, "time": tick_time}
                elif "pitch" in msg.type:
                    time = time_accum + msg.time
                    pitchs[msg.channel] = {"value": msg.pitch, "time": tick_time}
                else:
                    pass
                time_accum += msg.time
                for plugin in self.middles:
                    try:
                        plugin.execute(self)
                    except BaseException as e:
                        logging.warning("中间件 %s 引发了异常：%s" % (plugin, e))
                        logging.critical("构建已终止。")

        self.parsed_msgs.sort(key=lambda n: n["tick"])
        logging.debug(f"平均浮点舍入秒差距={time_diff_sum / len(self.parsed_msgs)}")
        logging.info("读取事件完成。")

    def build_parsed(self):
        self.built_cmds.clear()

        self.build_count = 0
        self.y_index = 0
        self.tick_cache = list()
        self.tick = 0

        logging.info("构建已读取的 %d 条事件。" % len(self.parsed_msgs))

        for self.tick in range(self.parsed_msgs[-1]["tick"] + 1):
            self.build_index = self.build_count % self.wrap_length
            self.wrap_index = self.build_count // self.wrap_length

            if (self.build_count + 1) % self.wrap_length == 0:
                self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index, chain=False,
                                   auto=False,
                                   command=self.set_red_block_code(1 - self.wrap_length, -1, 1))
                self.y_index += 1
            else:
                self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index, chain=False,
                                   auto=False,
                                   command=self.set_red_block_code(1, -1, 0))
                self.y_index += 1

            self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                               command=self.set_air_block_code(0, -2, 0))
            self.y_index += 1

            try:
                while self.parsed_msgs[0]["tick"] == self.tick:
                    self.tick_cache.append(self.parsed_msgs.pop(0))
            except IndexError:
                break

            for message in self.tick_cache:
                if message["type"] == "note_on":
                    self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                       command=self.play_soma_code(message["prog"], message["note"], message["v"],
                                                                   message["pan"], message["pitch"]))
                    self.y_index += 1
                elif message["type"] == "note_off":
                    self.set_cmd_block(x_shift=self.build_index, y_shift=self.y_index, z_shift=self.wrap_index,
                                       command=self.stop_soma_code(message["prog"], message["note"]))
                    self.y_index += 1

            for plugin in self.plugins:
                try:
                    plugin.execute(self)
                except BaseException as e:
                    logging.warning("插件 %s 引发了异常：%s" % (plugin, e))
                    logging.critical("构建已终止。")
                    raise e

            self.build_count += 1
            self.y_index = 0

            if self.tick % 5E2 == 0:
                logging.info("已构建 %d 游戏刻, 共计 %d 游戏刻。" % (self.tick, self.parsed_msgs[-1]["tick"] + 1))
            self.tick_cache.clear()

        logging.info("构建事件完成。")
        logging.info("这首音乐预计将有 %f 秒长。" % (self.tick / 20))

    @staticmethod
    def play_soma_code(program, note, v=255, pan=64, pitch=1):
        abs_pan = (pan - 64) / 32
        l_r = - abs_pan
        f_b = 2 - abs(abs_pan)
        rel_v = v / 255
        return f"execute as @a at @s run playsound {program}.{note} voice @s ^{l_r} ^ ^{f_b} {rel_v} {pitch}"

    @staticmethod
    def stop_soma_code(program, note):
        return f"execute as @a at @s run stopsound @s voice {program}.{note}"

    def set_cmd_block(self, x_shift, y_shift, z_shift, chain=True, repeat=False, auto=True, command="", facing="up"):
        type_def = (("chain_" if chain else "") + ("repeat_" if repeat else "")) * (0 if repeat and auto else 1)
        auto_def = str(bool(auto)).lower()
        self.built_cmds.append(f'setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:{type_def}command_block[facing=\
{facing}]{{auto: {auto_def}, Command: "{command}", LastOutput: false, TrackOutput: false}} replace\n')

    @staticmethod
    def set_red_block_code(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:redstone_block replace"

    @staticmethod
    def set_air_block_code(x_shift, y_shift, z_shift):
        return f"setblock ~{x_shift} ~{y_shift} ~{z_shift} minecraft:air replace"

    def write_built(self, wp):
        logging.info("写入已构建的 %d 条指令。" % (length := len(self.built_cmds)))
        if length >= 65536:
            logging.warning("注意，由于您的音乐函数长于默认允许的最大值（65536），请尝试键入以下指令。")
            logging.info("试试这个：/gamerule maxCommandChainLength %d" % (length + 1))

        os.makedirs(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions"), exist_ok=True)
        with open(os.path.join(wp, r"datapacks\MCDI\pack.mcmeta"), "w") as file:
            file.write('{"pack":{"pack_format":233,"description":"Made by MCDI, a project by kworker(FrankYang)."}}')
        with open(os.path.join(wp, r"datapacks\MCDI\data\mcdi\functions\music.mcfunction"), "w") as file:
            file.writelines(self.built_cmds)
        logging.info("写入指令完成。")
        logging.info("要运行音乐函数，键入：'/reload'")
        logging.info("接着键入： '/function mcdi:music'")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    gen = Generator(MIDI_DIR, tick_time=TICK_RATE, drum_enabled=DRUM_ENABLED, pan_enabled=PAN_ENABLED,
                    gvol_enabled=GLOBAL_VOLUME_ENABLED, pitch_enabled=PITCH_ENABLED, pitch_factor=PITCH_FACTOR,
                    volume_factor=VOLUME_FACTOR, plugins=PLUGINS, middles=MIDDLEWARES)
    gen.parse_tracks()
    gen.build_parsed()
    gen.write_built(DATA_DIR)
