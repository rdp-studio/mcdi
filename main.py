import argparse
import importlib
import os

from mid.core import InGameGenerator, RealTimeGenerator
from mid.middles import Middle
from mid.plugins import Plugin

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="kworker的红石音乐生成器，MCDI。")
    parser.add_argument("--type", default="rt")  # Generate type
    parser.add_argument("--midi")  # MIDI path
    parser.add_argument("--save")  # World path
    parser.add_argument("--plugins", default="")  # Plugins
    parser.add_argument("--middles", default="")  # Middles
    parser.add_argument("--tick", default=20)  # Tick rate
    parser.add_argument("--frontend", default="soma.Soma")  # Frontend
    parser.add_argument("--kwargs", default="")  # Additional keyword args
    args = parser.parse_args()

    type_ = args.type

    midi = args.midi
    if midi is None or not os.path.isfile(midi):
        raise RuntimeError("--midi 选定的文件不存在。")

    save = args.save
    if save is None or not os.path.isdir(save):
        raise RuntimeError("--save 选定的目录不存在。")

    tick = args.tick
    try:
        tps = float(tick)
    except ValueError:
        raise RuntimeError("--tick 没有给出浮点数。")

    plugins, packages = args.plugins, {}
    split = lambda x: os.path.splitext(x)
    files = os.listdir("./mid/plugins")
    for package, ext in map(split, files):
        if package.startswith("__") or ext != ".py": continue  # Invalid pkg
        packages[package] = importlib.import_module(f"mid.plugins.{package}")
    try:
        plugins = eval(f"[{plugins}]", packages)
    except NameError:
        raise RuntimeError("--plugins 指定的插件包/类不存在。")
    for i in plugins:
        if not isinstance(i, Plugin):
            raise RuntimeError("--plugins 指定了无效的中间件包/类。")

    middles, packages = args.middles, {}
    split = lambda x: os.path.splitext(x)
    files = os.listdir("./mid/middles")
    for package, ext in map(split, files):
        if package.startswith("__") or ext != ".py": continue  # Invalid pkg
        packages[package] = importlib.import_module(f"mid.middles.{package}")
    try:
        middles = eval(f"[{middles}]", packages)
    except NameError:
        raise RuntimeError("--middles 指定的中间件包/类不存在。")
    for i in middles:
        if not isinstance(i, Middle):
            raise RuntimeError("--middles 指定了无效的中间件包/类。")

    frontend = args.frontend
    try:
        package, klass = frontend.split(".")
        package = importlib.import_module(f"mid.frontends.{package}")
        frontend_class = getattr(package, klass)
    except (ValueError, ImportError, AttributeError):
        raise RuntimeError("--frontend 指定的前端包/类不存在。")

    gen_kwargs = args.kwargs
    try:
        gen_kwargs = eval("{%s}" % gen_kwargs)
    except Exception as e:
        raise RuntimeError(f"--kwargs 的格式不正确：{e}")

    if type_ == "rt":
        generator = RealTimeGenerator(fp=midi, plugins=plugins, **gen_kwargs)
    elif type_ == "ig":
        generator = InGameGenerator(fp=midi, frontend=frontend, middles=middles, plugins=plugins, **gen_kwargs)
    else:
        raise RuntimeError("--type 既不是'rt'（MIDIOut++）也不是'ig'（原版资源包）。")
    generator.auto_tick_rate(base=tick)
    if type_ == "ig":
        generator.make_note_links()
    generator.loaded_messages()
    generator.build_messages()
    generator.write_datapack(save)
