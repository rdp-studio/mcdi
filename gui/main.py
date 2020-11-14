import _queue
import importlib
import multiprocessing
import os
import pkgutil
import string
import sys
import threading
import time
import traceback
import uuid
import webbrowser
from multiprocessing import shared_memory

import yaml
import yaml.parser
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog, QApplication

sys.path.append("..")
import mid.frontends
from gui.core import HtmlGuiWindow
from mid.core import InGameGenerator, RealTimeGenerator
from mid.frontends import Frontend
from mid.middles import Middle
from mid.plugins import Plugin


def write_shm_text(shm: shared_memory.SharedMemory, text: str) -> None:
    data = bytearray(text, "utf8", "ignore")
    shm.buf[:1024] = data.ljust(1024, b"\0")


def read_shm_text(shm: shared_memory.SharedMemory) -> str:
    data = shm.buf.tobytes()
    index = data.index(b"\0")
    return data[:index].decode("utf8", "ignore")


def write_shm_long(shm: shared_memory.SharedMemory, val: int) -> None:
    data = val.to_bytes(8, "big", signed=True)
    shm.buf[:8] = data.ljust(8, b"\0")


def read_shm_long(shm: shared_memory.SharedMemory) -> int:
    data = shm.buf.tobytes()
    return int.from_bytes(data, "big", signed=True)


def eval_or_null(*args, **kwargs):
    # noinspection PyBroadException
    try:
        return eval(*args, **kwargs)
    except BaseException:
        return NotImplemented


class MainWindow(HtmlGuiWindow):
    GITHUB_URL = "https://github.com/FrankYang6921/mcdi/"
    BILIBILI_URL = "https://space.bilibili.com/21743452/"
    FRIEND_URL = "https://rsm.cool/s/"
    ISSUES_URL = GITHUB_URL + "issues/new/"

    DAEMON_INTERVAL = .05

    default_config = {
        "func_namespace": "mcdi",
        "minecraft_path": "",
        "version_selected": "",
        "world_selected": "",
        "fast_copy_func": True,
        "shared_home": False,
        "midi": {
            "generate_type": "ig",
            "path": "",
            "auto_adjust": {
                "is_enabled": True,
                "tolerance": 2.0,
                "step": .1,
                "base": 20,
            },
            "plugins": {},
            "middles": {},
            "frontend": "soma.Soma",
            "wrap_length": 128,
            "blank_ticks": 0.0,
            "use_func": False,
            "auto_func": True,
            "tick_rate": 20,
            "tick_scale": 1.0,
            "note_links": True,
            "overrides": {
                "program": False,
                "gvol": False,
                "phase": False,
                "pitch": False
            },
            "volume_factor": 1.,
            "pitch_factor": 1.,
        },
        "bitmap": {
            "generate_type": "blks",
            "path": "",
            "generate_axis": "XY",
            "reversed_axis": False,
            "color_space": "RGB",
            "particle_name": "minecraft:end_rod",
        }
    }

    def __init__(self, *args, **kwargs):
        os.chdir(os.path.dirname(sys.argv[0]))

        super(MainWindow, self).__init__(
            "main.html", r".\static", r".\templates", *args, **kwargs
        )

        self.setWindowTitle("Minecraft音乐生成器：MCDI")
        self.setWindowIcon(QIcon(r".\logo.png"))
        self.doc_ready_flag = threading.Event()

        self("#about-l1").bind("onclick", lambda: webbrowser.open(self.GITHUB_URL))
        self("#about-l2").bind("onclick", lambda: webbrowser.open(self.BILIBILI_URL))
        self("#about-l3").bind("onclick", lambda: webbrowser.open(self.FRIEND_URL))
        self("#issue").bind("onclick", lambda: webbrowser.open(self.ISSUES_URL))

        self("#midi-path").bind("ondblclick", self.browse_midi_path)
        self("#bmp-path").bind("ondblclick", self.browse_bmp_path)
        self("#plugin-chk-btn").bind("onclick", self.reload_plugin_cfg)
        self("#plugin-cfg-btn").bind("onclick", self.open_plugin_cfg)
        self("#middle-chk-btn").bind("onclick", self.reload_middle_cfg)
        self("#middle-cfg-btn").bind("onclick", self.open_middle_cfg)

        self("#func-ns").bind("onblur", lambda: self.validate_func_ns())
        self("#mc-path").bind("onblur", lambda: self.validate_mc_path())
        self("#minecraft-ver").bind("onchange", lambda: self.validate_mc_path())
        self("#bmp-mc-save").bind("onchange", lambda: self.validate_mc_path())
        self("#midi-mc-save").bind("onchange", lambda: self.validate_mc_path())
        self("#mojang-launcher").bind("onclick", lambda: self.validate_mc_path())
        self("#mc-path").bind("ondblclick", self.browse_mc_path)

        self("body").bind("onmousemove", self.load_objects)

        self("#midi-run").bind("onclick", self.midi_run)
        self("#midi-stop").bind("onclick", self.midi_stop)

        self.loaded_plugins = {}
        self.loaded_middles = {}
        self.loaded_frontends = {}
        self.objects_loaded = False

        self.midi_process = None
        self.midi_daemon = None
        self.bmp_process = None
        self.bmp_daemon = None
        self.midi_daemon_lock = threading.Event()
        self.bmp_daemon_lock = threading.Event()

        self.config_tree = {}
        self.config_worker = None
        self.load_config()

    def dump_default_cfg(self):
        with open("config.yml", "w", encoding="utf8") as file:
            yaml.dump(self.default_config, file, yaml.CDumper)

    def load_config(self):
        if not os.path.exists("config.yml"):
            self.dump_default_cfg()

        file = open("config.yml", "r", encoding="utf8")
        try:
            self.config_tree.update(yaml.load(file, yaml.CFullLoader))
        except yaml.parser.ParserError:
            self.send_toast("您的配置文件似乎不是有效的YAML文件。")
            self.dump_default_cfg()
            self.load_config()
            return None
        file.close()

        def map_checkbutton(this, value, selector):
            if value:
                this(f"{selector}").setprop("checked", "checked")
            else:
                this.execute_js(f'$("{selector}").removeAttr("checked")')

        def map_radiobutton(this, value, mapping):
            assert value in mapping
            this(f"{mapping[value]}").setprop("checked", "checked")

        def worker(this: MainWindow):
            this.doc_ready_flag.wait()
            try:
                map_checkbutton(this, this.config_tree["shared_home"], "#mojang-launcher")
                map_checkbutton(this, this.config_tree["midi"]["auto_adjust"]["is_enabled"], "#auto-adjust")
                map_checkbutton(this, this.config_tree["fast_copy_func"], "#fast-copy-func")
                map_radiobutton(this, this.config_tree["midi"]["generate_type"], {
                    "ig": "#midi-type-ig",
                    "rt": "#midi-type-rt"
                })
                map_radiobutton(this, this.config_tree["bitmap"]["generate_type"], {
                    "blks": "#bmp-type-blks-color",
                    "text": "#bmp-type-text-color",
                    "prtcl_mono": "#bmp-type-prtcl-mono",
                    "prtcl_color": "#bmp-type-prtcl-color"
                })
                map_radiobutton(this, this.config_tree["bitmap"]["generate_axis"], {
                    "XY": "#axis-xy",
                    "YZ": "#axis-yz",
                    "XZ": "#axis-xz"
                })
                map_checkbutton(this, this.config_tree["bitmap"]["reversed_axis"], "#axis-reversed")
                map_radiobutton(this, this.config_tree["bitmap"]["color_space"], {
                    "RGB": "#color-rgb",
                    "HSV": "#color-hsv"
                })
                this("#particle").value = this.config_tree["bitmap"]["particle_name"]
                this("#wrap-length").value = this.config_tree["midi"]["wrap_length"]
                this("#blank-ticks").value = this.config_tree["midi"]["blank_ticks"]
                map_radiobutton(this, this.config_tree["midi"]["use_func"] + this.config_tree["midi"]["auto_func"] * 2,
                                {
                                    0: "#no-fa",
                                    1: "#use-fa",
                                    2: "#at-fa",
                                    3: "#use-fa"
                                })
                map_checkbutton(this, this.config_tree["midi"]["note_links"], "#note-links")
                this("#tick-rate").value = this.config_tree["midi"]["tick_rate"]
                this("#tick-scale").value = this.config_tree["midi"]["tick_scale"]
                this("#tolerance").value = this.config_tree["midi"]["auto_adjust"]["tolerance"]
                this("#step").value = this.config_tree["midi"]["auto_adjust"]["step"]
                this("#base").value = this.config_tree["midi"]["auto_adjust"]["base"]
                map_checkbutton(this, this.config_tree["midi"]["overrides"]["program"], "#use-program")
                map_checkbutton(this, this.config_tree["midi"]["overrides"]["gvol"], "#use-g-volume")
                map_checkbutton(this, this.config_tree["midi"]["overrides"]["phase"], "#use-phase")
                map_checkbutton(this, this.config_tree["midi"]["overrides"]["pitch"], "#use-pitch")
                this("#pitch-factor").value = this.config_tree["midi"]["pitch_factor"]
                this("#volume-factor").value = this.config_tree["midi"]["volume_factor"]
                this("#midi-path").value = this.config_tree["midi"]["path"]
                this("#bmp-path").value = this.config_tree["bitmap"]["path"]
                this.validate_func_ns(this.config_tree["func_namespace"])
                this.validate_mc_path(
                    this.config_tree["minecraft_path"],
                    version=this.config_tree["version_selected"],
                    world=this.config_tree["world_selected"]
                )

                this.execute_js("M.updateTextFields();")

                assert "plugins" in this.config_tree["midi"] and isinstance(this.config_tree["midi"]["plugins"], dict)
                assert "middles" in this.config_tree["midi"] and isinstance(this.config_tree["midi"]["middles"], dict)
                assert "frontend" in this.config_tree["midi"]
            except (TypeError, KeyError, AssertionError):
                this.send_toast("您的配置文件似乎不是有效的MCDI配置。")
                this.dump_default_cfg()
                this.load_config()
                return None

        self.config_worker = threading.Thread(target=worker, args=(self,))
        self.config_worker.setDaemon(True)
        self.config_worker.start()
        return self.config_worker

    @staticmethod
    def midi_worker_main(mem1, mem2, cfg, q):
        # noinspection PyBroadException
        try:
            shm1 = shared_memory.SharedMemory(mem1)
            shm2 = shared_memory.SharedMemory(mem2)

            def update_status(txt, val):
                write_shm_text(shm1, txt)
                write_shm_long(shm2, val)

            update_status("<b>准备：</b>加载插件。", 0)

            plugins = []

            def _load_module(type_):
                _names = cfg['midi'][f'{type_}s']

                for name in _names:
                    _pkg_name, klass_name = name.split(".")
                    _pkg = importlib.import_module(
                        f"mid.{type_}s.{_pkg_name}"
                    )
                    klass = getattr(_pkg, klass_name)
                    args = cfg['midi'][f'{type_}s'][name]
                    real_args = {}

                    for arg, value in args.items():
                        arg = arg.replace(f"#{type_}-cfg-{_pkg_name}-{klass_name}-", "")
                        if not (isinstance(value, str) and value.strip()):
                            continue
                        real_args[arg] = j if (j := eval_or_null(value, vars(_pkg))) \
                                              is not NotImplemented else value
                    try:
                        instance = klass(**real_args)
                    except TypeError:
                        q.put(
                            f"猜测：无法初始化“{name}”，因为参数类型不正确或缺少。\n{traceback.format_exc()}")
                        return None
                    except AttributeError:
                        q.put(
                            f"猜测：无法初始化“{name}”，因为找不到指定的类或模块。\n{traceback.format_exc()}")
                        return None
                    yield instance

            plugins.extend(_load_module("plugin"))

            fp = cfg["midi"]["path"]
            ig = InGameGenerator

            if cfg["midi"]["generate_type"] == "rt":
                update_status("<b>准备：</b>创建生成器实例。", 0)
                try:
                    gen = RealTimeGenerator(fp=fp, plugins=plugins, namespace=cfg["func_namespace"])
                except FileNotFoundError:
                    q.put(f"猜测：无法创建生成器实例，因为无法找到MIDI文件。\n{traceback.format_exc()}")
                    return None
                except PermissionError:
                    q.put(f"猜测：无法创建生成器实例，因为无法读取MIDI文件。\n{traceback.format_exc()}")
                    return None
                except (OSError, IOError):
                    q.put(f"猜测：无法创建生成器实例，因为MIDI文件无效。\n{traceback.format_exc()}")
                    return None


            elif cfg["midi"]["generate_type"] == "ig":
                update_status("<b>准备：</b>加载前端。", 0)

                names = cfg['midi']['frontend']
                pkg_name = names.split(".")[0]
                frn_name = names.split(".")[1]
                pkg = importlib.import_module(
                    f"mid.frontends.{pkg_name}"
                )
                try:
                    frontend = getattr(pkg, frn_name)
                except AttributeError:
                    q.put(
                        f"猜测：无法初始化前端“{frn_name}”，因为找不到指定的前端。\n{traceback.format_exc()}")
                    return None

                update_status("<b>准备：</b>加载中间件。", 0)
                middles = []
                middles.extend(_load_module("middle"))

                update_status("<b>准备：</b>创建生成器实例。", 0)
                try:
                    gen = InGameGenerator(
                        fp=fp, frontend=frontend, plugins=plugins, middles=middles, namespace=cfg["func_namespace"]
                    )
                except FileNotFoundError:
                    q.put(f"猜测：无法创建生成器实例，因为无法找到MIDI文件。\n{traceback.format_exc()}")
                    return None
                except PermissionError:
                    q.put(f"猜测：无法创建生成器实例，因为无法读取MIDI文件。\n{traceback.format_exc()}")
                    return None
                except (OSError, IOError):
                    q.put(f"猜测：无法创建生成器实例，因为MIDI文件无效。\n{traceback.format_exc()}")
                    return None

                try:
                    gen.gvol_enabled = not cfg["midi"]["overrides"]["gvol"]
                    gen.prog_enabled = not cfg["midi"]["overrides"]["program"]
                    gen.phase_enabled = not cfg["midi"]["overrides"]["phase"]
                    gen.pitch_enabled = not cfg["midi"]["overrides"]["pitch"]
                    gen.pitch_factor = float(cfg["midi"]["pitch_factor"])
                    gen.volume_factor = float(cfg["midi"]["volume_factor"])
                except ValueError:
                    q.put(f"猜测：无法配置生成器实例，因为无法解析浮点数。\n{traceback.format_exc()}")
                    return None

            else:
                raise RuntimeError("不合法的生成类型。")

            try:
                gen.wrap_length = round(float(cfg["midi"]["wrap_length"]))
                gen._use_function_array = cfg["midi"]["use_func"]
                gen._auto_function_array = cfg["midi"]["auto_func"]
                gen.blank_ticks = round(float(cfg["midi"]["blank_ticks"]))
                gen.tick_rate = float(cfg["midi"]["tick_rate"])
                gen.tick_scale = float(cfg["midi"]["tick_scale"])
            except ValueError:
                q.put(f"猜测：无法配置生成器实例，因为无法解析浮点数。\n{traceback.format_exc()}")
                return None

            if (i := cfg["midi"]["auto_adjust"])["is_enabled"]:
                update_status("<b>生成：</b>自动调整参数。", 20)
                try:
                    gen.auto_tick_rate(
                        base=float(i["base"]),
                        step=float(i["step"]),
                        tolerance=float(i["tolerance"])
                    )
                except ValueError:
                    q.put(f"猜测：无法自动调整参数，因为无法解析浮点数。\n{traceback.format_exc()}")
                    return None

            if cfg["midi"]["note_links"] and isinstance(gen, ig):
                update_status("<b>生成：</b>预加载音符链。", 40)
                gen.make_note_links()

            update_status("<b>生成：</b>加载音符。", 60)
            gen.load_messages()

            update_status("<b>生成：</b>构造音符。", 80)
            gen.build_messages()

            if cfg["shared_home"]:
                saves = os.path.join(cfg["minecraft_path"], "saves")
            else:
                saves = os.path.join(cfg["minecraft_path"], "versions", cfg["version_selected"], "saves")
            world = os.path.join(saves, cfg["world_selected"])

            update_status("<b>生成：</b写入数据包。", 100)
            try:
                gen.write_datapack(world)
            except FileNotFoundError:
                q.put(f"猜测：无法写入数据包，因为世界路径不存在。\n{traceback.format_exc()}")
                return None

            update_status("<b>结束：</b>销毁生成器实例。", 100)
            del gen

        except Exception:
            q.put(traceback.format_exc())
        else:
            q.put(NotImplementedError())

    def daemon_worker(self, lk, shm1, shm2):
        lk.set()

        pend = "<b>挂起：</b>等待子进程响应…"

        while lk.is_set():
            if txt := read_shm_text(shm1):
                self("#midi-gen-details").inner_html = txt
            else:
                self("#midi-gen-details").inner_html = pend
            self("#midi-gen-progress").set_css(
                "width", f"{read_shm_long(shm2)}%"
            )
            time.sleep(self.DAEMON_INTERVAL)

    def midi_run(self):
        self("#midi-gen-overlay").fade_in()
        shm1, shm2 = shared_memory.SharedMemory(create=True, size=1024), shared_memory.SharedMemory(create=True, size=8)

        self.save_config()
        c = self.config_tree.copy()
        q = multiprocessing.Queue()
        self.midi_process = multiprocessing.Process(target=self.midi_worker_main, args=(shm1.name, shm2.name, c, q))
        self.midi_process.start()
        self.midi_daemon = threading.Thread(target=self.daemon_worker, args=(self.midi_daemon_lock, shm1, shm2))
        self.midi_daemon.start()

        self.midi_process.join()
        self.midi_daemon_lock.clear()

        try:
            ret = q.get(block=False)
            if isinstance(ret, str):
                self("#stack").inner_text = ret.strip()
                self.execute_js(
                    f'M.Modal.getInstance(document.getElementById("modal-failure")).open();'
                )
                self.send_toast("生成失败。")
            else:
                self.send_toast("生成完成。")
        except _queue.Empty:
            self.send_toast("生成中断。")

        self("#midi-gen-overlay").fade_out()

    def midi_stop(self):
        if self.midi_process is not None:
            self.midi_process.terminate()

    def save_config(self):
        def get_radiobutton(mapping):
            for selector in mapping:
                if self(selector).getprop("checked"):
                    return mapping[selector]

        def get_checkbutton(selector):
            return self(selector).getprop("checked")

        self.config_tree["bitmap"]["color_space"] = get_radiobutton({"#color-rgb": "RGB", "#color-hsv": "HSV"})
        self.config_tree["bitmap"]["generate_axis"] = get_radiobutton({
            '#axis-xy': 'XY',
            '#axis-yz': 'YZ',
            '#axis-xz': 'XZ'
        })
        self.config_tree["bitmap"]["generate_type"] = get_radiobutton({
            '#bmp-type-blks-color': 'blks',
            '#bmp-type-text-color': 'text',
            '#bmp-type-prtcl-mono': 'prtcl_mono',
            '#bmp-type-prtcl-color': 'prtcl_color'
        })
        self.config_tree["bitmap"]["particle_name"] = self("#particle").value
        self.config_tree["bitmap"]["reversed_axis"] = get_checkbutton("#axis-reversed")
        self.config_tree["fast_copy_func"] = get_checkbutton("#fast-copy-func")
        self.config_tree["func_namespace"] = self("#func-ns").value
        self.config_tree["midi"]["auto_adjust"]["base"] = self("#base").value
        self.config_tree["midi"]["auto_adjust"]["is_enabled"] = get_checkbutton("#auto-adjust")
        self.config_tree["midi"]["auto_adjust"]["step"] = self("#step").value
        self.config_tree["midi"]["auto_adjust"]["tolerance"] = self("#tolerance").value
        self.config_tree["midi"]["auto_func"], self.config_tree["midi"]["use_func"] = get_radiobutton({
            "#no-fa": (False, False),
            "#use-fa": (False, True),
            "#at-fa": (True, False),
        })
        self.config_tree["midi"]["blank_ticks"] = self("#blank-ticks").value
        self.config_tree["midi"]["frontend"] = self("#frontend-list").value
        self.config_tree["midi"]["generate_type"] = get_radiobutton({
            "#midi-type-ig": "ig",
            "#midi-type-rt": "rt"
        })
        self.config_tree["midi"]["path"] = self("#midi-path").value
        self.config_tree["bitmap"]["path"] = self("#bmp-path").value

        self.config_tree["midi"]["plugins"].clear()
        for pkg, i in self.loaded_plugins.items():
            for plugin in i:
                if self(f"#p-{pkg}-{plugin['name']}").getprop("selected"):
                    self.config_tree["midi"]["plugins"][(p := f"{pkg}.{plugin['name']}")] = {}
                    plugin_class = getattr(importlib.import_module(f"mid.plugins.{pkg}"), plugin['name'])
                    for key in plugin_class.__init__.__annotations__.keys():
                        key = f"#plugin-cfg-{pkg}-{plugin['name']}-{key}"
                        self.config_tree["midi"]["plugins"][p][key] = self(key).value
                        val = self(key).value
                        if not val.startswith("TypeError"):
                            self.config_tree["midi"]["plugins"][p][key] = val
                        else:
                            self.config_tree["midi"]["plugins"][p][key] = None

        self.config_tree["midi"]["middles"].clear()
        for pkg, i in self.loaded_middles.items():
            for middle in i:
                if self(f"#p-{pkg}-{middle['name']}").getprop("selected"):
                    self.config_tree["midi"]["middles"][(p := f"{pkg}.{middle['name']}")] = {}
                    middle_class = getattr(importlib.import_module(f"mid.middles.{pkg}"), middle['name'])
                    for key in middle_class.__init__.__annotations__.keys():
                        key = f"#middle-cfg-{pkg}-{middle['name']}-{key}"
                        val = self(key).value
                        if not val.startswith("TypeError"):
                            self.config_tree["midi"]["middles"][p][key] = val
                        else:
                            self.config_tree["midi"]["middles"][p][key] = None

        self.config_tree["midi"]["note_links"] = get_checkbutton("#note-links")
        self.config_tree["midi"]["overrides"]["program"] = get_checkbutton("#use-program")
        self.config_tree["midi"]["overrides"]["gvol"] = get_checkbutton("#use-g-volume")
        self.config_tree["midi"]["overrides"]["phase"] = get_checkbutton("#use-phase")
        self.config_tree["midi"]["overrides"]["pitch"] = get_checkbutton("#use-pitch")
        self.config_tree["midi"]["pitch_factor"] = self("#pitch-factor").value
        self.config_tree["midi"]["tick_rate"] = self("#tick-rate").value
        self.config_tree["midi"]["tick_scale"] = self("#tick-scale").value
        self.config_tree["midi"]["volume_factor"] = self("#volume-factor").value
        self.config_tree["midi"]["wrap_length"] = self("#wrap-length").value
        self.config_tree["minecraft_path"] = self("#mc-path").value
        self.config_tree["shared_home"] = get_checkbutton("#mojang-launcher")
        self.config_tree["version_selected"] = self("#minecraft-ver").value
        self.config_tree["world_selected"] = self("#midi-mc-save").value

        with open("config.yml", "w", encoding="utf8") as file:
            yaml.dump(self.config_tree, file, yaml.SafeDumper)

    def closeEvent(self, event):
        if not self.objects_loaded:
            event.accept()  # No config saving procedure.
            return None

        self.config_worker = threading.Thread(target=self.save_config)
        self.config_worker.start()
        self.config_worker.join()
        event.accept()

    def browse_midi_path(self):
        self("#midi-path").value = QFileDialog.getOpenFileUrl(
            self, "浏览MIDI路径", filter="MID 文件(*.mid)\0*.mid\0\0"
        )[0].toString().strip("file:///")

    def browse_bmp_path(self):
        self("#bmp-path").value = QFileDialog.getOpenFileUrl(
            self, "浏览图像路径", filter="PNG 文件(*.png)\0*.png\0\0"
        )[0].toString().strip("file:///")

    def browse_mc_path(self):
        self.validate_mc_path(QFileDialog.getExistingDirectory(self, "浏览.minecraft/ 路径"), True)

    def validate_func_ns(self, func_ns=None):
        if func_ns is None:
            func_ns = self("#func-ns").value
        else:
            self("#func-ns").value = func_ns

        if not func_ns.strip():
            self.send_toast("函数命名空间为空。")
            return None

        if any(map(lambda i: i not in string.digits + string.ascii_lowercase + "-_", func_ns)):
            self.send_toast("函数命名空间非法。")
            return None

        self.send_toast("函数命名空间合法。")

    def validate_mc_path(self, path=None, version=None, world=None):
        i = None

        if path is None:
            path = self("#mc-path").value
        else:
            self("#mc-path").value = path
        if version is None:
            version = self("#minecraft-ver").value
        if world is None:
            world = self("#midi-mc-save").value

        self("#minecraft-ver").empty()
        self("#bmp-mc-save").empty()
        self("#midi-mc-save").empty()

        if not os.path.exists(path):
            self.send_toast("Minecraft路径不存在。")
            self("#mojang-launcher").setprop("disabled", "disabled")
            self("#minecraft-ver").setprop("disabled", "disabled")
            self("#midi-mc-save").setprop("disabled", "disabled")
            self("#bmp-mc-save").setprop("disabled", "disabled")

            self.execute_js(
                '$("#minecraft-ver").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            self.execute_js(
                '$("#bmp-mc-save").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            self.execute_js(
                '$("#midi-mc-save").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')

        elif os.path.exists(os.path.join(path, "versions")) and (i := os.listdir(os.path.join(path, "versions"))):
            self.send_toast("检测到了Minecraft客户端。")
            self.execute_js('$("#mojang-launcher").removeAttr("disabled")')
            self.execute_js('$("#minecraft-ver").removeAttr("disabled")')
            self.execute_js('$("#midi-mc-save").removeAttr("disabled")')
            self.execute_js('$("#bmp-mc-save").removeAttr("disabled")')

            for v in i:
                self.execute_js(f'$("#minecraft-ver").append("<option value=\'{v}\'>{v}</option>");')
            if version in i:
                self("#minecraft-ver").value = version

            if self("#mojang-launcher").getprop("checked"):
                path = os.path.join(path, "saves")
            else:
                path = os.path.join(path, "versions", version, "saves")
            try:
                for w in (i := os.listdir(path)):
                    self.execute_js(
                        f'$("#bmp-mc-save").append("<option value=\'{w}\'>{w}</option>");')
                    self.execute_js(
                        f'$("#midi-mc-save").append("<option value=\'{w}\'>{w}</option>");')
                if world in i:
                    self("#midi-mc-save").value = world
                    self("#bmp-mc-save").value = world
                self.send_toast("检测到了Minecraft世界。")
            except (FileNotFoundError, OSError):
                self.send_toast("未检测到Minecraft世界。")

        elif os.path.exists(os.path.join(path, "world")) and os.path.exists(os.path.join(path, "server.properties")):
            self.send_toast("检测到了Minecraft服务端。")
            self("#mojang-launcher").setprop("disabled", "disabled")
            self("#minecraft-ver").setprop("disabled", "disabled")
            self("#midi-mc-save").setprop("disabled", "disabled")
            self("#bmp-mc-save").setprop("disabled", "disabled")

            self.execute_js(
                '$("#minecraft-ver").append("<option value=\'\' disabled selected>- 选择一个Minecraft客户端以开始配置 -</option>");')
            self.execute_js(
                '$("#bmp-mc-save").append("<option value=\'\' disabled selected>- 选择一个Minecraft客户端以开始配置 -</option>");')
            self.execute_js(
                '$("#midi-mc-save").append("<option value=\'\' disabled selected>- 选择一个Minecraft客户端以开始配置 -</option>");')

        else:
            self.send_toast("Minecraft路径不合法。")
            self("#mojang-launcher").setprop("disabled", "disabled")
            self("#minecraft-ver").setprop("disabled", "disabled")
            self("#midi-mc-save").setprop("disabled", "disabled")
            self("#bmp-mc-save").setprop("disabled", "disabled")

            self.execute_js(
                '$("#minecraft-ver").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            self.execute_js(
                '$("#bmp-mc-save").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            self.execute_js(
                '$("#midi-mc-save").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')

        self.execute_js("M.AutoInit();")

    @staticmethod
    def _load_module(path, parent, base_class):
        modules = {}

        for i in pkgutil.iter_modules(path):
            modules[(pkg := i.name)] = list()
            module_pkg = importlib.import_module(
                f"mid.{parent}.{pkg}"
            )
            for attr in dir(module_pkg):
                module = getattr(module_pkg, attr)

                if isinstance(module, type) and issubclass(module, base_class) and module is not base_class:
                    modules[pkg].append({
                        "pkg": pkg, "name": module.__name__, "author": module.__author__, "doc": module.__doc__
                    })

        return modules

    def load_objects(self):
        if self.objects_loaded:
            return None

        self("body").unbind("onmousemove")
        self.doc_ready_flag.set()
        self.config_worker.join()
        target_plugins = self.config_tree["midi"]["plugins"]
        target_middles = self.config_tree["midi"]["middles"]
        target_frontend = self.config_tree["midi"]["frontend"]

        plugins, middles, frontends = {}, {}, {}
        self.loaded_plugins.clear()
        self.loaded_middles.clear()
        self.loaded_frontends.clear()

        plugins.update(self._load_module(mid.plugins.__path__, "plugins", Plugin))
        middles.update(self._load_module(mid.middles.__path__, "middles", Middle))
        frontends.update(self._load_module(mid.frontends.__path__, "frontends", Frontend))

        for pkg in plugins.keys():
            random_id = uuid.uuid4()
            self.execute_js(
                f'$("#plugin-list").append("<optgroup id=\'{random_id}\' label=\'包：{pkg}\'></optgroup>")')

            for plugin in plugins[pkg]:
                s = "selected='selected'" if f'{pkg}.{plugin["name"]}' in target_plugins else ''
                self.execute_js(
                    f'$("#{random_id}").append("<option id=\'p-{pkg}-{plugin["name"]}\' value=\'{pkg}.{plugin["name"]}\' {s}>插件：<code>'
                    f'{plugin["name"]}</code> by <i>{plugin["author"]}</i>: <q>{plugin["doc"]}</q></option>")'
                )

        self.reload_plugin_cfg()

        for pkg in middles.keys():
            random_id = uuid.uuid4()
            self.execute_js(
                f'$("#middle-list").append("<optgroup id=\'{random_id}\' label=\'包：{pkg}\'></optgroup>")')

            for middle in middles[pkg]:
                s = "selected='selected'" if f'{pkg}.{middle["name"]}' in target_middles else ''
                self.execute_js(
                    f'$("#{random_id}").append("<option id=\'m-{pkg}-{middle["name"]}\' value=\'{pkg}.{middle["name"]}\' {s}>中间件：<code>'
                    f'{middle["name"]}</code> by <i>{middle["author"]}</i>: <q>{middle["doc"]}</q></option>")'
                )

        self.reload_middle_cfg()

        for pkg in frontends.keys():
            random_id = uuid.uuid4()
            self.execute_js(
                f'$("#frontend-list").append("<optgroup id=\'{random_id}\' label=\'包：{pkg}\'></optgroup>")')

            for frontend in frontends[pkg]:
                s = "selected='selected'" if f'{pkg}.{frontend["name"]}' == target_frontend else ''
                self.execute_js(
                    f'$("#{random_id}").append("<option value=\'{pkg}.{frontend["name"]}\' {s}>前端：<code>'
                    f'{frontend["name"]}</code> by <i>{frontend["author"]}</i>: <q>{frontend["doc"]}</q></option>")')

        self.loaded_plugins.update(plugins)
        self.loaded_middles.update(middles)
        self.loaded_frontends.update(frontends)

        self.execute_js("M.AutoInit();")
        self.objects_loaded = True

    def reload_plugin_cfg(self):
        plugins = self.execute_js('$("#plugin-list").val();')

        self("#plugin-cfg-list").empty()

        if not plugins:
            self("#plugin-cfg-list").append('<option value="" disabled selected>- 至少选择一个插件以开始配置 -</option>')

        for pkg in self.loaded_plugins.keys():
            for plugin in self.loaded_plugins[pkg]:
                self(f"#modal-plugin-{pkg}-{plugin['name']}").remove()

        for plugin in plugins:
            pkg, plugin = plugin.split(".")
            self("#plugin-cfg-list").append(f'<option value="{pkg}.{plugin}">包“{pkg}”中的插件：“{plugin}”</option>')

            plugin_class = getattr(importlib.import_module(f"mid.plugins.{pkg}"), plugin)

            data = ""

            for key, value in plugin_class.__init__.__annotations__.items():
                k = f"#plugin-cfg-{pkg}-{plugin}-{key}"
                val = self.config_tree["midi"]["plugins"][f"{pkg}.{plugin}"][k] \
                    if f"{pkg}.{plugin}" in \
                       self.config_tree["midi"]["plugins"] and \
                       k in self.config_tree["midi"]["plugins"][f"{pkg}.{plugin}"] and \
                       self.config_tree["midi"]["plugins"][f"{pkg}.{plugin}"][k] \
                       is not None else ""
                val.replace('"', r'\"')

                data += f'''
                    <div class="input-field col s12">
                        <input id="plugin-cfg-{pkg}-{plugin}-{key}" value="{val}">
                        <label for="plugin-cfg-{pkg}-{plugin}-{key}">参数：{key}</label>
                        <span class="helper-text">{value}</span>
                    </div>
                '''

            self.execute_js(f'''$("body").prepend(`
            <div id="modal-plugin-{pkg}-{plugin}" class="modal">
                <div class="modal-content">
                    <h4>配置包“{pkg}”中的插件“{plugin}”</h4><div class="row">{data}</div>
                </div>
                <div class="modal-footer">
                    <a href="#" class="modal-close waves-effect btn-flat">保存更改</a>
                </div>
            </div>
            `);''')

        self.execute_js("M.AutoInit();")

    def open_plugin_cfg(self):
        plugin = self.execute_js('$("#plugin-cfg-list").val();')

        if not plugin:
            self.send_toast("您似乎还没有选择插件。在选择完毕后，请点击“刷新”。")
            return None

        pkg, plugin = plugin.split(".")

        self.execute_js(f'M.Modal.getInstance(document.getElementById("modal-plugin-{pkg}-{plugin}")).open();')

    def reload_middle_cfg(self):
        middles = self.execute_js('$("#middle-list").val();')

        self("#middle-cfg-list").empty()

        if not middles:
            self("#middle-cfg-list").append('<option value="" disabled selected>- 至少选择一个中间件以开始配置 -</option>')

        for pkg in self.loaded_middles.keys():
            for middle in self.loaded_middles[pkg]:
                self(f"#modal-middle-{pkg}-{middle['name']}").remove()

        for middle in middles:
            pkg, middle = middle.split(".")
            self("#middle-cfg-list").append(f'<option value="{pkg}.{middle}">包“{pkg}”中的中间件：“{middle}”</option>')

            middle_class = getattr(importlib.import_module(f"mid.middles.{pkg}"), middle)

            data = ""

            for key, value in middle_class.__init__.__annotations__.items():
                k = f"#middle-cfg-{pkg}-{middle}-{key}"
                val = self.config_tree["midi"]["middles"][f"{pkg}.{middle}"][k] \
                    if f"{pkg}.{middle}" in \
                       self.config_tree["midi"]["middles"] and \
                       k in self.config_tree["midi"]["middles"][f"{pkg}.{middle}"] and \
                       self.config_tree["midi"]["middles"][f"{pkg}.{middle}"][k] \
                       is not None else ""
                val.replace('"', r'\"')

                data += f'''
                    <div class="input-field col s12">
                        <input id="middle-cfg-{pkg}-{middle}-{key}" value="{val}">
                        <label for="middle-cfg-{pkg}-{middle}-{key}">参数：{key}</label>
                        <span class="helper-text">{value}</span>
                    </div>
                '''

            self.execute_js(f'''$("body").prepend(`
            <div id="modal-middle-{pkg}-{middle}" class="modal">
                <div class="modal-content">
                    <h4>配置包“{pkg}”中的中间件“{middle}”</h4><div class="row">{data}</div>
                </div>
                <div class="modal-footer">
                    <a href="#" class="modal-close waves-effect btn-flat">保存更改</a>
                </div>
            </div>
            `);''')

        self.execute_js("M.AutoInit();")

    def open_middle_cfg(self):
        middle = self.execute_js('$("#middle-cfg-list").val();')

        if not middle:
            self.send_toast("您似乎还没有选择中间件。在选择完毕后，请点击“刷新”。")
            return None

        pkg, middle = middle.split(".")

        self.execute_js(f'M.Modal.getInstance(document.getElementById("modal-middle-{pkg}-{middle}")).open();')

    def send_toast(self, message):
        message = message.replace("\"", r"\"")
        self.execute_js(
            f'M.toast({{html: "{message}"}})'
        )


if __name__ == '__main__':
    multiprocessing.freeze_support()
    application = QApplication(sys.argv)
    MainWindow().show()  # The entrance
    application.exit(application.exec_())
