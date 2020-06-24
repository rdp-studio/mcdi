import json
import logging
import os
import re
import threading
import time
from urllib.error import HTTPError
from urllib.request import urlopen

from gui_base import *
import mido

class CustomLogger(logging.Handler):
    def __init__(self, parent: MainFrame):
        super().__init__()
        self.parent = parent

    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
            self.parent.StatusBar.SetStatusText(msg, 0)
        except Exception:
            self.handleError(record)

class TrackPanel(wx.Panel):
    def __init__(self, parent, track_name, track_inst, display_name=None):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL);
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_INACTIVECAPTIONTEXT))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

        TrackSizer = wx.BoxSizer(wx.VERTICAL)

        self.TrackLabel = wx.StaticText(self, wx.ID_ANY, u"音轨名："+track_name, wx.DefaultPosition, wx.DefaultSize, 0)
        self.TrackLabel.Wrap(-1)

        TrackSizer.Add(self.TrackLabel, 0, wx.ALL, 5)

        self.InstLabel = wx.StaticText(self, wx.ID_ANY, u"乐器名："+track_inst, wx.DefaultPosition, wx.DefaultSize, 0)
        self.InstLabel.Wrap(-1)

        TrackSizer.Add(self.InstLabel, 0, wx.ALL, 5)

        self.TrackChooser = wx.Choicebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.CHB_DEFAULT)
        TrackSizer.Add(self.TrackChooser, 1, wx.EXPAND | wx.ALL, 5)
        self.frontends_panes=[]

        self.SetSizer(TrackSizer)
        self.Layout()
        self.Centre(wx.BOTH)
        self.frontends_init()
        self.frontends_panes=[]
        if display_name==None:
            parent.AddPage(self, track_name)
        else:
            parent.AddPage(self, display_name)

    def frontends_init(self):
        from midi_project import frontends

        for frontend_item in dir(frontends):
            frontend: frontends.Frontend = getattr(frontends, frontend_item)
            if type(f := frontend) is type and f is not frontends.Frontend and issubclass(f, frontends.Frontend):
                self.frontends_panes.append(ConfigPage(self.TrackChooser, frontend))

        for pane in self.frontends_panes:
            pane.bind();

class ConfigPage(wx.Panel):
    def __init__(self, parent, object_):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.object_ = object_
        self.Container = wx.BoxSizer(wx.VERTICAL)

        self.Configure = wx.ListCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT)

        self.Configure.AppendColumn("形参名")
        self.Configure.AppendColumn("类型/注释")
        self.Configure.AppendColumn("值")

        self.param_values = dict()
        parameters = object_.__init__.__annotations__
        parameter_keys = parameters.keys()

        if not parameter_keys:
            index = self.Configure.InsertItem(65535, "*无参数*")
            self.Configure.SetItem(index, 1, "*不可用*")
            self.Configure.SetItem(index, 2, "*不可用*")
        else:
            for key in parameter_keys:
                index = self.Configure.InsertItem(65535, key)
                self.Configure.SetItem(index, 1, f"“{parameters[key]}”")
                self.Configure.SetItem(index, 2, "*未指定*")

        self.Container.Add(self.Configure, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(self.Container)
        self.Layout()
        self.Container.Fit(self)
        parent.AddPage(self, f"{object_.__name__} ({object_.__doc__ if object_.__doc__ else '...'})", False)

    @property
    def params(self):
        return_dict = dict()
        for key in self.param_values.keys():
            value = self.param_values[key]
            if re.match(r"^-?[1-9]\d*$", value):
                return_dict[key] = int(value)
            elif re.match(r"^-?([1-9]\d*\.\d*|0\.\d*[1-9]\d*|0?\.0+|0)$", value):
                return_dict[key] = float(value)
            elif re.match(r"^(\{.*\}|\[.*\]|\(.*\))$", value):
                return_dict[key] = eval(value)
            elif value in ("True", "False", "None"):
                return_dict[key] = eval(value)
            else:
                return_dict[key] = str(value)
        return return_dict

    def bind(self):
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self._edit_params, self.Configure)

    def _edit_params(self, event=None):
        selection = self.Configure.GetFirstSelected()
        name = self.Configure.GetItem(selection, 0).GetText()
        if re.match(r"^\*.*\*$", name):
            wx.MessageBox("这个项目没有参数。", "提示", wx.ICON_INFORMATION)
            return None
        description = self.Configure.GetItem(selection, 1).GetText()
        value = self.Configure.GetItem(selection, 2).GetText()
        if re.match(r"^\*.*\*$", value):
            dialog = wx.TextEntryDialog(self, description, f"更改参数“{name}”……")
        else:
            dialog = wx.TextEntryDialog(self, description, f"更改参数“{name}”……", value)
        if dialog.ShowModal() == wx.ID_OK:
            value = dialog.GetValue()
            self.Configure.SetItem(selection, 2, value)
            self.param_values[name] = value


class MainWindow(MainFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_panes = []
        self.plugin_panes = []
        self.middle_panes = []
        self.plugins_init()
        self.middles_init()
        self.check_identifier_state()
        self.check_namespace_state()
        self._bind_events()
        self._config_loop()
        time.sleep(0.5)
        if os.path.exists(self.MIDIPathPicker.GetPath()):
            self.midi_update()
        try:
            response = urlopen("http://frankyang.com.cn:2121/projects/mcdi/assets/about.html")
            self.MIDIPageAboutHTML.SetPage(response.read().decode("gbk"))
        except HTTPError:
            self.MIDIPageAboutHTML.SetPage("<h1>:(</h1><p>暂时无法加载关于页面。<p>")

    def _bind_events(self):
        self.Bind(wx.EVT_BUTTON, self.midi_run, self.Run)

        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.midi_update, self.MIDIPathPicker)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.dot_mc_update, self.DotMCPathPicker)
        self.Bind(wx.EVT_CHECKBOX, self.dot_mc_update, self.MCVersionShowOld)
        self.Bind(wx.EVT_CHOICE, self.world_update, self.MCVersionPicker)
        self.Bind(wx.EVT_CHECKBOX, self.world_update, self.MCVersionDependent)
        self.Bind(wx.EVT_CHECKBOX, self.check_namespace_state, self.PackNamespaceAuto)
        self.Bind(wx.EVT_CHECKBOX, self.check_identifier_state, self.PackIdentifierAuto)

        for pane in self.frontend_panes + self.plugin_panes + self.middle_panes:
            pane.bind()

    def _config_loop(self):
        def main_thread(self: MainWindow):
            if os.path.exists("config.json"):
                with open("config.json", "r") as config_file:
                    config = json.loads(config_file.read())
                try:
                    self.MIDIPathPicker.SetPath(config["midi_path"])
                    self.DotMCPathPicker.SetPath(config["dot_mc_path"])
                    self.PackNamespaceInput.SetValue(config["pack_namespace"])
                    self.PackIdentifierInput.SetValue(config["pack_identifier"])
                    self.MCVersionShowOld.SetValue(config["show_old_mc_ver"])
                    self.MCVersionDependent.SetValue(config["no_independent"])
                    self.FlexDurationSpin.SetValue(config["flex_duration"])
                    self.FlexToleranceSpin.SetValue(config["flex_tolerance"])
                    self.FlexSteppingSpin.SetValue(config["flex_stepping"])
                    self.StaticDurationSpin.SetValue(config["static_duration"])
                    self.StaticTickRateSpin.SetValue(config["static_tick_rate"])
                    self.MIDIPageTimingPages.SetSelection(config["timing_mode"])
                    self.EffectAllowPan.SetValue(config["do_pan"]),
                    self.EffectAllowGVol.SetValue(config["do_gvol"]),
                    self.EffectAllowPitch.SetValue(config["do_pitch"]),
                    self.EffectVolumeFactorSpin.SetValue(config["volume_factor"]),
                    self.EffectPitchFactorSpin.SetValue(config["pitch_factor"]),
                    self.EffectDoLongAnalysis.SetValue(config["do_long_analysis"]),
                    self.LongAnalysisThresholdSpin.SetValue(config["long_threshold"]),
                    self.MaxTickNoteSpin.SetValue(config["max_tick_note"]),
                    self.WrapLengthSpin.SetValue(config["wrap_length"]),
                    self.EffectFunctionBased.SetValue(config["function_based"]),
                    self._config_init(config)
                except KeyError as e:
                    wx.MessageBox(f"配置文件不合法：{e}", "警告", wx.OK | wx.ICON_WARNING)
                except BaseException as e:
                    import traceback
                    wx.MessageBox(f"未捕获的错误：{traceback.format_exc()}", "错误", wx.OK | wx.ICON_ERROR)
                logging.info("准备就绪。")
            while True:
                version_selection = self.MCVersionPicker.GetSelection()
                ver = self.MCVersionPicker.GetItems()[version_selection] if version_selection >= 0 else None
                world_selection = self.MCWorldPicker.GetSelection()
                world = self.MCWorldPicker.GetItems()[world_selection] if world_selection >= 0 else None
                config = {
                    "midi_path": self.MIDIPathPicker.GetPath(),
                    "dot_mc_path": self.DotMCPathPicker.GetPath(),
                    "pack_namespace": self.PackNamespaceInput.GetValue(),
                    "pack_identifier": self.PackIdentifierInput.GetValue(),
                    "show_old_mc_ver": self.MCVersionShowOld.GetValue(),
                    "no_independent": self.MCVersionDependent.GetValue(),
                    "mc_version": ver, "mc_world_name": world,
                    "flex_duration": self.FlexDurationSpin.GetValue(),
                    "flex_tolerance": self.FlexToleranceSpin.GetValue(),
                    "flex_stepping": self.FlexSteppingSpin.GetValue(),
                    "static_duration": self.StaticDurationSpin.GetValue(),
                    "static_tick_rate": self.StaticTickRateSpin.GetValue(),
                    "timing_mode": self.MIDIPageTimingPages.GetSelection(),
                    "do_pan": self.EffectAllowPan.GetValue(),
                    "do_gvol": self.EffectAllowGVol.GetValue(),
                    "do_pitch": self.EffectAllowPitch.GetValue(),
                    "volume_factor": self.EffectVolumeFactorSpin.GetValue(),
                    "pitch_factor": self.EffectPitchFactorSpin.GetValue(),
                    "do_long_analysis": self.EffectDoLongAnalysis.GetValue(),
                    "long_threshold": self.LongAnalysisThresholdSpin.GetValue(),
                    "max_tick_note": self.MaxTickNoteSpin.GetValue(),
                    "wrap_length": self.WrapLengthSpin.GetValue(),
                    "function_based": self.EffectFunctionBased.GetValue(),
                }
                with open("config.json", "w") as config_file:
                    config_file.write(json.dumps(config))
                time.sleep(1)

        thread = threading.Thread(target=main_thread, args=(self,))
        thread.setDaemon(daemonic=True) or thread.start()

    def _config_init(self, config: dict):
        self.dot_mc_update()
        items = self.MCVersionPicker.GetItems()
        if config["mc_version"] in items and config["mc_version"]:
            self.MCVersionPicker.SetSelection(items.index(config["mc_version"]))
        self.world_update()
        items = self.MCWorldPicker.GetItems()
        if config["mc_world_name"] in items and config["mc_world_name"]:
            self.MCWorldPicker.SetSelection(items.index(config["mc_world_name"]))
        self.check_namespace_state()
        self.check_identifier_state()

    def dot_mc_update(self, event=None):
        dot_mc_path = self.DotMCPathPicker.GetPath()

        if not os.path.exists(versions_path := os.path.join(dot_mc_path, "versions")):
            if dot_mc_path:
                wx.MessageBox(f"选定的'.minecraft'目录（{dot_mc_path}）不合法。", "警告", wx.OK | wx.ICON_WARNING)
            else:
                wx.MessageBox(f"尚未选定'.minecraft'目录。", "提示", wx.OK | wx.ICON_INFORMATION)
            self.MCVersionPicker.SetItems(["*.minecraft/ 无效*"])
        elif not (versions := os.listdir(versions_path)):
            wx.MessageBox(f"选定的'versions'目录（{versions_path}）不合法。", "警告", wx.OK | wx.ICON_WARNING)
            self.MCVersionPicker.SetItems(["*versions/ 无效*"])
        elif self.MCVersionShowOld.GetValue():
            self.versions_path = versions_path
            self.MCVersionPicker.SetItems(versions)
        else:
            self.versions_path = versions_path
            versions = filter(lambda x: re.match(r".*1\.1[3-6].*", x), versions)
            self.MCVersionPicker.SetItems(list(versions))

    def midi_update(self, event=None):
        midi_file=mido.MidiFile(self.MIDIPathPicker.GetPath())
        self.TrackPicker.DeleteAllPages()
        for i, track in enumerate(midi_file.tracks):
          TrackPanel(self.TrackPicker, track.name, "Not implemented", f"Track {i}");

    def world_update(self, event=None):
        if not hasattr(self, "versions_path"):
            wx.MessageBox(f"尚未选定'versions'目录。", "提示", wx.OK | wx.ICON_INFORMATION)
            self.MCWorldPicker.SetItems(["*versions/ 无效*"])
        elif self.MCVersionPicker.GetSelection() == -1:
            wx.MessageBox(f"尚未选定Minecraft版本。", "提示", wx.OK | wx.ICON_INFORMATION)
            self.MCWorldPicker.SetItems(["*请先选择版本*"])
        elif self.MCVersionDependent.GetValue():
            self.saves_path = os.path.join(*os.path.split(self.versions_path)[:-1], "saves")
            try:
                if li := os.listdir(self.saves_path):
                    self.MCWorldPicker.SetItems(li)
                else:
                    wx.MessageBox(f"暂无有效世界。", "提示", wx.OK | wx.ICON_INFORMATION)
                    self.MCWorldPicker.SetItems(["*暂无有效世界*"])
            except FileNotFoundError:
                wx.MessageBox(f"选定的存档路径（{self.saves_path}）不存在。", "警告", wx.OK | wx.ICON_WARNING)
                self.MCWorldPicker.SetItems(["*saves/ 无效*"])
        else:
            version = self.MCVersionPicker.GetItems()[self.MCVersionPicker.GetSelection()]
            self.saves_path = os.path.join(self.versions_path, version, "saves")
            try:
                if li := os.listdir(self.saves_path):
                    self.MCWorldPicker.SetItems(li)
                else:
                    wx.MessageBox(f"暂无有效世界。", "提示", wx.OK | wx.ICON_INFORMATION)
                    self.MCWorldPicker.SetItems(["*暂无有效世界*"])
            except FileNotFoundError:
                wx.MessageBox(f"选定的存档路径（{self.saves_path}）不存在。", "警告", wx.OK | wx.ICON_WARNING)
                self.MCWorldPicker.SetItems(["*saves/ 无效*"])

    def check_namespace_state(self, event=None):
        if self.PackNamespaceAuto.GetValue():
            self.PackNamespaceInput.SetValue("mcdi")
            self.PackNamespaceInput.Disable()
        else:
            self.PackNamespaceInput.Enable()

    def check_identifier_state(self, event=None):
        if self.PackIdentifierAuto.GetValue():
            self.PackIdentifierInput.SetValue("func")
            self.PackIdentifierInput.Disable()
        else:
            self.PackIdentifierInput.Enable()

    def plugins_init(self):
        from midi_project import plugins

        for plugin_item in dir(plugins):
            plugin: plugins.Plugin = getattr(plugins, plugin_item)
            if type(p := plugin) is type and p is not plugins.Plugin and issubclass(p, plugins.Plugin):
                self.plugin_panes.append(ConfigPage(self.PluginsPicker, plugin))

                self.PluginsList.Append(
                    f"{plugin.__name__} - {plugin.__doc__ if plugin.__doc__ else '?'}"
                    f" - By {plugin.__author__}" if hasattr(plugin, "__author__") else "")

    def middles_init(self):
        from midi_project import middlewares

        for middle_item in dir(middlewares):
            middle: middlewares.Middleware = getattr(middlewares, middle_item)
            if type(m := middle) is type and m is not middlewares.Middleware and issubclass(m, middlewares.Middleware):
                self.middle_panes.append(ConfigPage(self.MiddlesPicker, middle))

                self.MiddlesList.Append(
                    f"{middle.__name__} - {middle.__doc__ if middle.__doc__ else '?'}"
                    f" - By {middle.__author__}" if hasattr(middle, "__author__") else "")

    def midi_run(self, event=None):
        def main_thread(self: MainWindow, event):
            from midi_project import frontends, plugins, middlewares
            from midi_project.core import Generator

            self.Run.Disable()

            try:
                plugin_list = []
                indexes = self.PluginsList.GetCheckedItems()
                plugin_strings = self.PluginsList.GetItems()
                for index in indexes:
                    params = self.plugin_panes[index].params
                    plugin_name = plugin_strings[index].split("-")[0].strip()
                    if (plugin := getattr(plugins, plugin_name, None)) is None:
                        wx.MessageBox(f"选定的插件（{plugin_name}）不存在。", "错误", wx.OK | wx.ICON_ERROR)
                        raise StopIteration
                    plugin_list.append(plugin(**params))

                middle_list = []
                indexes = self.MiddlesList.GetCheckedItems()
                middle_strings = self.MiddlesList.GetItems()
                for index in indexes:
                    params = self.middle_panes[index].params
                    middle_name = middle_strings[index].split("-")[0].strip()
                    if (middle := getattr(middlewares, middle_name, None)) is None:
                        wx.MessageBox(f"选定的中间件（{middle_name}）不存在。", "错误", wx.OK | wx.ICON_ERROR)
                        raise StopIteration
                    middle_list.append(middle(**params))

                callback = lambda x, y: self.ProgressBar.SetValue(int(x / y * 100))

                midi_path = self.MIDIPathPicker.GetPath()
                if not os.path.exists(midi_path):
                    if midi_path:
                        wx.MessageBox(f"选定的MIDI路径（{midi_path}）不存在。", "错误", wx.OK | wx.ICON_ERROR)
                    else:
                        wx.MessageBox(f"尚未选定MIDI路径。", "提示", wx.OK | wx.ICON_INFORMATION)
                    raise StopIteration

                frontend_text = self.FrontendPicker.GetPageText(index := self.FrontendPicker.GetSelection())
                frontend_class = re.findall(r"^(.+?)\s\(.*\)$", frontend_text)[0]
                frontend = getattr(frontends, frontend_class)(**self.frontend_panes[index].params)

                self.ProgressBar.SetValue(0)
                logging.info("正在读取MIDI文件...")
                wrap_length = self.WrapLengthSpin.GetValue()
                namespace = self.PackNamespaceInput.GetValue()
                identifier = self.PackIdentifierInput.GetValue()
                generator = Generator(midi_path, frontend, namespace, identifier, wrap_length, plugins=plugin_list,
                                      middles=middle_list)
                self.ProgressBar.SetValue(100)

                self.ProgressBar.SetValue(0)
                selection = self.MIDIPageTimingPages.GetSelection()
                if selection == 0:
                    logging.info("正在计算弹性时长...")
                    expected_len = float(self.FlexDurationSpin.GetValue())
                    tolerance = float(self.FlexToleranceSpin.GetValue())
                    stepping = float(self.FlexSteppingSpin.GetValue())
                    generator.tick_analysis(expected_len, tolerance, stepping, progress_callback=callback)
                elif selection == 1:
                    generator.tick_rate = float(self.StaticTickRateSpin.GetValue())
                elif selection == 2:
                    logging.info("正在计算固定时长...")
                    expected_len = float(self.FlexDurationSpin.GetValue())
                    generator.tick_analysis(expected_len, 0, 1, progress_callback=callback)

                if self.EffectDoLongAnalysis.GetValue():
                    logging.info("正在分析长音...")
                    threshold = float(self.LongAnalysisThresholdSpin.GetValue())
                    generator.long_note_analysis(threshold, progress_callback=callback)

                logging.info("正在加载MIDI事件...")
                pan_enabled = self.EffectAllowPan.GetValue()
                gvol_enabled = self.EffectAllowGVol.GetValue()
                pitch_enabled = self.EffectAllowPitch.GetValue()
                pitch_factor = self.EffectPitchFactorSpin.GetValue()
                volume_factor = self.EffectVolumeFactorSpin.GetValue()
                generator.load_events(pan_enabled, gvol_enabled, pitch_enabled, pitch_factor, volume_factor)
                self.ProgressBar.SetValue(100)

                logging.info("正在生成指令...")

                limitation = self.MaxTickNoteSpin.GetValue()
                # function_based = self.EffectFunctionBased.GetValue()
                generator.build_events(progress_callback=callback, limitation=limitation)
                self.ProgressBar.SetValue(100)

                if not hasattr(self, "saves_path"):
                    wx.MessageBox(f"请先选择游戏版本和世界名称。", "提示", wx.OK | wx.ICON_INFORMATION)
                    raise StopIteration
                world_name = self.MCWorldPicker.GetStringSelection()
                world_path = os.path.join(self.saves_path, world_name)

                self.ProgressBar.SetValue(0)
                logging.info("正在写入指令...")
                generator.write_func(wp=world_path)
                self.ProgressBar.SetValue(100)

                logging.info("生成完成，准备就绪。")

            except StopIteration:
                logging.warning("生成遇到错误。准备就绪。")
                self.ProgressBar.SetValue(0)
            except BaseException as e:
                import traceback
                logging.warning("生成遇到错误。准备就绪。")
                self.ProgressBar.SetValue(0)
                wx.MessageBox(f"未捕获的错误：{traceback.format_exc()}", "错误", wx.OK | wx.ICON_ERROR)
            finally:
                self.Run.Enable()

        thread = threading.Thread(target=main_thread, args=(self, event))
        thread.setDaemon(daemonic=True) or thread.start()


if __name__ == '__main__':
    app = wx.App()
    frame = MainWindow(None)

    logger = logging.getLogger("")
    handler = CustomLogger(frame)
    logger.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    frame.Show(True)
    app.MainLoop()
