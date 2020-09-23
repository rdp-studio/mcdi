import importlib
import multiprocessing
import os
import string
import sys
import threading
import time
import uuid
import webbrowser

import mido
import requests
from PyQt5.QtWidgets import QFileDialog, QApplication

from gui.core import HtmlGuiWindow, run_in_new_thread
from mid.agent import Server

sys.path.append("..")


def midi_play(file, output=None):
    port = mido.open_output(output)
    midi = mido.MidiFile(file)

    for message in midi.play():
        port.send(message)

    port.reset()
    port.close()


def get_mac_address():
    return uuid.UUID(int=uuid.getnode()).hex[-12:]


class OOBEWindow(HtmlGuiWindow):
    def __init__(self, *args, **kwargs):
        super(OOBEWindow, self).__init__(
            "oobe.html", *args, **kwargs
        )

        self.setWindowTitle("Minecraft工具箱 - MCDI")

        self("#wizard-finish").bind("onclick", self.finish)
        self("#wizard-skip").bind("onclick", self.skip)
        self("#wizard-next").bind("onclick", self.verify)
        self("#wizard-exit").bind("onclick", self.exit)
        self("#mc-path-open").bind("onclick", self.browse_mc_path)

    def verify(self):
        page = self.execute_js('wizard.pageId;')

        if page == 1:
            client_state = self("#mc-type-client").getprop("checked")
            server_state = self("#mc-type-server").getprop("checked")

            if not (client_state or server_state):
                self.execute_js('M.toast({html: "您似乎还没有选择您的Minecraft类型。"});')
                return None

            if client_state:
                self.mc_type = "CLIENT"
            elif server_state:
                self.mc_type = "SERVER"

        elif page == 2:
            path = self("#mc-path").value

            if not os.path.exists(path):
                self.execute_js('M.toast({html: "您选择的游戏路径似乎不存在。"});')
                return None

            if self.mc_type == "CLIENT":
                if not os.path.exists(os.path.join(path, "versions")):
                    self.execute_js('M.toast({html: "您选择的游戏路径似乎没有安装Minecraft客户端。"});')
                    return None
                if not (i := os.listdir(os.path.join(path, "versions"))):
                    self.execute_js('M.toast({html: "您选择的游戏路径似乎没有安装Minecraft客户端。"});')
                    return None

                js_code = '$("#mc-ver").empty();'
                for version in i:
                    js_code += f'$("#mc-ver").append("<option value=\'{version}\'>{version}</option>");'
                js_code += '$("#mc-ver").prepend("<option value=\'\' disabled selected>-</option>");'

                self.execute_js(js_code)

                self.dotmc_path = path
                return self.execute_js('wizard.fadeToPage(3);')

            elif self.mc_type == "SERVER":
                if not os.path.exists(os.path.join(path, "world")):
                    self.execute_js('M.toast({html: "您选择的游戏路径似乎没有安装Minecraft服务端。"});')
                    return None
                if not os.path.exists(os.path.join(path, "server.properties")):
                    self.execute_js('M.toast({html: "您选择的游戏路径似乎没有安装Minecraft服务端。"});')
                    return None

                self.dotmc_path = path
                return self.execute_js('wizard.fadeToPage(4);')

        elif page == 3:
            version = self("#mc-ver").value

            if not version:
                self.execute_js('M.toast({html: "您似乎还没有选择您的Minecraft版本。"});')
                return None

            self.version = version
            self.version_path = os.path.join(self.dotmc_path, version)

        self.execute_js('wizard.fadeNext();')

    def finish(self):
        r_state = self("#midi-type-ig").getprop("checked")
        b_state = self("#midi-type-rt").getprop("checked")

        if not (r_state or b_state):
            self.execute_js('M.toast({html: "您似乎还没有选择您的生成方式。"});')
            return None

        if r_state:
            self.midi_type = "IG"
        elif b_state:
            self.midi_type = "RT"

        self.auto_adjust = self("#auto-adjust").getprop("checked")

        self.exit()

    def skip(self):
        pass

    def exit(self):
        os._exit(0)

    def browse_mc_path(self):
        self("#mc-path").value = QFileDialog.getExistingDirectory(self, "浏览.minecraft/ 路径")


class MainWindow(HtmlGuiWindow):
    GITHUB_URL = "https://github.com/FrankYang6921/mcdi"
    BILIBILI_URL = "https://space.bilibili.com/21743452"
    FRIEND_URL = "https://rsm.cool/"

    REGISTER_SERVER = "http://localhost:8000/check/"

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(
            "main.html", *args, **kwargs
        )

        self.setWindowTitle("Minecraft工具箱 - MCDI")

        self("#about-l1").bind("onclick", lambda: webbrowser.open(self.GITHUB_URL))
        self("#about-l2").bind("onclick", lambda: webbrowser.open(self.BILIBILI_URL))
        self("#about-l3").bind("onclick", lambda: webbrowser.open(self.FRIEND_URL))

        self("#rtsv-midi-test").bind("onclick", self.midi_test)
        self("#rtsv-midi-stop").bind("onclick", self.midi_stop)

        self("#midi-path").bind("ondblclick", self.browse_midi_path)
        self("#plugin-chk-btn").bind("onclick", self.reload_plugin_cfg)
        self("#plugin-cfg-btn").bind("onclick", self.open_plugin_cfg)
        self("#middle-chk-btn").bind("onclick", self.reload_middle_cfg)
        self("#middle-cfg-btn").bind("onclick", self.open_middle_cfg)

        self("#vpr-path").bind("ondblclick", self.browse_vpr_path)

        self("#rtsv-midi-device").bind("onchange", self.update_midi_device)
        self("#rtsv-start-btn").bind("onclick", self.run_rt_server)
        self("#rtsv-stop-btn").bind("onclick", self.term_rt_server)

        self("#func-ns").bind("onblur", self.validate_func_ns)
        self("#mc-path").bind("ondblclick", self.browse_mc_path)
        self("#mc-path").bind("onblur", self.validate_mc_path)

        self(".fixed-action-btn").bind("onclick", self.load_objects)
        self(".load-objects-btn").bind("onclick", self.load_objects)

        self("#activate-btn").bind(
            "onclick", lambda: self.check_register(self("#register-code").value, True)
        )

        self.plugins = {}
        self.middles = {}

        self.objects_loaded = False
        self.midi_test_process = ...
        self.rt_server_thread = ...

        self.midi_device_ok = False
        self.server_path_ok = False
        self.server_opening = threading.Event()

        self.rt_server = ...

        os.chdir(os.path.join(os.path.split(__file__)[0], ".."))

        if os.path.exists("gui/$ACODE"):
            with open("gui/$ACODE", "rb") as file:
                code = file.read().decode("utf8")
            run_in_new_thread(lambda: self.check_register(code, False))

        else:
            run_in_new_thread(lambda: self.check_register("N/A", False))


    def check_register(self, code, triggered):
        os.chdir(os.path.join(os.path.split(__file__)[0], ".."))

        self("#activate-pend").show()
        self("#activate-ok").hide()
        self("#activate-fail").hide()
        self(".activate").hide()

        run_in_new_thread(lambda: self.execute_js(f'$("#register-code").text("{code}");'))
        try:
            data = requests.get(f"{self.REGISTER_SERVER}?mac={get_mac_address()}&key={code}")
        except requests.exceptions.ConnectionError:
            self.execute_js('M.toast({html: "无法连接到激活服务器。"});')
            self("#activate-fail").show()
            return self(".activate").show()

        json_data = data.json()

        self("#activate-pend").hide()
        if json_data["errno"] == 0:
            if triggered:
                self.execute_js('M.toast({html: "激活成功。"});')
            self("#activate-ok").show()
            self(".activate").hide()

        else:
            if json_data["errno"] == 1 and triggered:
                self.execute_js('M.toast({html: "该激活码不符合MCDI激活码格式。"});')
            elif json_data["errno"] == 2 and triggered:
                self.execute_js('M.toast({html: "该激活码未授权给对应的用户。"});')
            elif json_data["errno"] == 3 and triggered:
                self.execute_js('M.toast({html: "该激活码未于有效期限内使用。"});')
            elif json_data["errno"] == 4 and triggered:
                self.execute_js('M.toast({html: "该激活码未授权给对应的主机。"});')
            elif triggered:
                self.execute_js('M.toast({html: "激活服务器发生了内部错误。"});')

            self("#activate-fail").show()
            self(".activate").show()

        with open("gui/$ACODE", "wb") as file:
            file.write(code.encode("utf8"))

    def browse_midi_path(self):
        self("#midi-path").value = QFileDialog.getOpenFileUrl(
            self, "浏览MIDI路径", filter="MID 文件(*.mid)\0*.mid\0\0")[0].toString().strip("file:///")

    def browse_vpr_path(self):
        self("#vpr-path").value = QFileDialog.getOpenFileUrl(
            self, "浏览VPR路径", filter="VPR 文件(*.vpr)\0*.vpr\0\0")[0].toString().strip("file:///")

    def browse_mc_path(self):
        value = self("#mc-path").value = QFileDialog.getExistingDirectory(self, "浏览.minecraft/ 路径")
        self.validate_mc_path(value)

    def validate_func_ns(self, value=None):
        if value is None:
            value = self("#func-ns").value

        if not value.strip():
            self.execute_js('M.toast({html: "函数命名空间不能为空字符串。"});')
            return

        for i in value:
            if i not in string.digits + string.ascii_lowercase + "-_":
                self.execute_js('M.toast({html: "函数命名空间只能包含数字、小写字母、中划线与下划线。"});')
                return

    def validate_mc_path(self, value=None):
        if value is None:
            value = self("#mc-path").value

        self("#mc-ver").empty()

        if not os.path.exists(value):
            self.execute_js('M.toast({html: "您选择的游戏路径似乎不存在。"});')
            self.execute_js(
                '$("#mc-ver").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            return

        if os.path.exists(os.path.join(value, "versions")) and (i := os.listdir(os.path.join(value, "versions"))):
            self.execute_js('$("#mojang-launcher").removeAttr("disabled")')
            self.execute_js('$("#mc-ver").removeAttr("disabled")')
            for version in i:
                self.execute_js(f'$("#mc-ver").append("<option value=\'{version}\'>{version}</option>");')
            self.execute_js("M.AutoInit();")

        elif os.path.exists(os.path.join(value, "world")) and os.path.exists(os.path.join(value, "server.properties")):
            self("#mojang-launcher").setprop("disabled", "disabled")
            self("#mc-ver").setprop("disabled", "disabled")
            self.execute_js(
                '$("#mc-ver").append("<option value=\'\' disabled selected>- 在使用服务端时不可选择Minecraft版本。 -</option>");')
            self.execute_js("M.AutoInit();")

        else:
            self.execute_js('M.toast({html: "您选择的游戏路径似乎没有安装Minecraft（服务端或客户端）。"});')
            self.execute_js(
                '$("#mc-ver").append("<option value=\'\' disabled selected>- 键入或浏览一个合法的路径以开始配置 -</option>");')
            return

    def load_objects(self):
        os.chdir(os.path.join(os.path.split(__file__)[0], ".."))

        from mid.plugins import Plugin
        from mid.middles import Middle

        plugins, middles = {}, {}

        if self.objects_loaded:
            return None

        self.objects_loaded = True

        for file in os.listdir("./mid/plugins"):
            pkg, ext = os.path.splitext(file)

            if file == "__init__.py":
                continue
            if ext not in (".py", ".pyc"):
                continue

            plugin_pkg = importlib.import_module(f"mid.plugins.{pkg}")
            plugins[pkg] = []

            for attr in dir(plugin_pkg):
                plugin = getattr(plugin_pkg, attr)

                if isinstance(plugin, type) and issubclass(plugin, Plugin) and plugin is not Plugin:
                    plugins[pkg].append({
                        "pkg": pkg, "name": plugin.__name__, "author": plugin.__author__, "doc": plugin.__doc__
                    })

        for file in os.listdir("./mid/middles"):
            pkg, ext = os.path.splitext(file)

            if file == "__init__.py":
                continue
            if ext not in (".py", ".pyc"):
                continue

            middle_pkg = importlib.import_module(f"mid.middles.{pkg}")
            middles[pkg] = []

            for attr in dir(middle_pkg):
                middle = getattr(middle_pkg, attr)

                if isinstance(middle, type) and issubclass(middle, Middle) and middle is not Middle:
                    middles[pkg].append({
                        "pkg": pkg, "name": middle.__name__, "author": middle.__author__, "doc": middle.__doc__
                    })

        for pkg in plugins.keys():
            random_id = uuid.uuid4()

            self.execute_js(f'$("#plugin-list").append("<optgroup id=\'{random_id}\' label=\'包：{pkg}\'></optgroup>")')

            for plugin in plugins[pkg]:
                self.execute_js(
                    f'$("#{random_id}").append("<option value=\'{pkg}.{plugin["name"]}\'>插件：<code>{plugin["name"]}</code> by <i>{plugin["author"]}</i>: <q>{plugin["doc"]}</q></option>")')

        for pkg in middles.keys():
            random_id = uuid.uuid4()

            self.execute_js(f'$("#middle-list").append("<optgroup id=\'{random_id}\' label=\'包：{pkg}\'></optgroup>")')

            for middle in middles[pkg]:
                self.execute_js(
                    f'$("#{random_id}").append("<option value=\'{pkg}.{middle["name"]}\'>中间件：<code>{middle["name"]}</code> by <i>{middle["author"]}</i>: <q>{middle["doc"]}</q></option>")')

        self.plugins.update(plugins)
        self.middles.update(middles)

        midi_ports = mido.get_output_names()

        self("#rtsv-midi-device").empty()

        if not midi_ports:
            self.execute_js(
                f'$("#rtsv-midi-device").append("option value="" disabled selected>- 在您的系统中找不到MIDI设备 -</option>")')

        for port in midi_ports:
            port_name = "\x20".join(port.split()[:-1])
            self.execute_js(f'$("#rtsv-midi-device").append("<option value=\'{port}\'>{port_name}</option>")')

        self.execute_js("M.AutoInit();")

        self("#rtsv-midi-device").trigger("onchange")

        self(".preload").fade_out("slow")

    def reload_plugin_cfg(self):
        plugins = self.execute_js('$("#plugin-list").val();')

        self("#plugin-cfg-list").empty()

        if not plugins:
            self("#plugin-cfg-list").append('<option value="" disabled selected>- 至少选择一个插件以开始配置 -</option>')

        for pkg in self.plugins.keys():
            for plugin in self.plugins[pkg]:
                self(f"#modal-plugin-{pkg}-{plugin['name']}").remove()

        for plugin in plugins:
            pkg, plugin = plugin.split(".")
            self("#plugin-cfg-list").append(f'<option value="{pkg}.{plugin}">包“{pkg}”中的插件：“{plugin}”</option>')

            plugin_class = getattr(importlib.import_module(f"mid.plugins.{pkg}"), plugin)

            data = ""

            for key, value in plugin_class.__init__.__annotations__.items():
                data += f'''
                    <div class="input-field col s12">
                        <input id="plugin-cfg-{pkg}-{plugin}-{key}">
                        <label for="plugin-cfg-{pkg}-{plugin}-{key}">参数：{key}</label>
                        <span class="helper-text">{value}</span>
                    </div>
                '''

            self.execute_js(f'''$("body").prepend(`
            <div id="modal-plugin-{pkg}-{plugin}" class="modal">
                <div class="modal-content">
                    <h4>配置包“{pkg}”中的插件：“{plugin}”</h4>
                    <div class="row">
                        {data}
                    </div>
                </div>
                <div class="modal-footer">
                    <a href="#" class="modal-close waves-effect btn-flat">关闭</a>
                </div>
            </div>
            `);''')

        self.execute_js("M.AutoInit();")

    def open_plugin_cfg(self):
        plugin = self.execute_js('$("#plugin-cfg-list").val();')

        if not plugin:
            self.execute_js('M.toast({html: "您似乎还没有选择插件。在选择完毕后，请点击“刷新”。"});')
            return None

        pkg, plugin = plugin.split(".")

        self.execute_js(f'M.Modal.getInstance(document.getElementById("modal-plugin-{pkg}-{plugin}")).open();')

    def reload_middle_cfg(self):
        middles = self.execute_js('$("#middle-list").val();')

        self("#middle-cfg-list").empty()

        if not middles:
            self("#middle-cfg-list").append('<option value="" disabled selected>- 至少选择一个中间件以开始配置 -</option>')

        for pkg in self.middles.keys():
            for middle in self.middles[pkg]:
                self(f"#modal-middle-{pkg}-{middle['name']}").remove()

        for middle in middles:
            pkg, middle = middle.split(".")
            self("#middle-cfg-list").append(f'<option value="{pkg}.{middle}">包“{pkg}”中的中间件：“{middle}”</option>')

            middle_class = getattr(importlib.import_module(f"mid.middles.{pkg}"), middle)

            data = ""

            for key, value in middle_class.__init__.__annotations__.items():
                data += f'''
                    <div class="input-field col s12">
                        <input id="middle-cfg-{pkg}-{middle}-{key}">
                        <label for="middle-cfg-{pkg}-{middle}-{key}">参数：{key}</label>
                        <span class="helper-text">{value}</span>
                    </div>
                '''

            self.execute_js(f'''$("body").prepend(`
            <div id="modal-middle-{pkg}-{middle}" class="modal">
                <div class="modal-content">
                    <h4>配置包“{pkg}”中的中间件：“{middle}”</h4>
                    <div class="row">
                        {data}
                    </div>
                </div>
                <div class="modal-footer">
                    <a href="#" class="modal-close waves-effect btn-flat">关闭</a>
                </div>
            </div>
            `);''')

        self.execute_js("M.AutoInit();")

    def open_middle_cfg(self):
        middle = self.execute_js('$("#middle-cfg-list").val();')

        if not middle:
            self.execute_js('M.toast({html: "您似乎还没有选择中间件。在选择完毕后，请点击“刷新”。"});')
            return None

        pkg, middle = middle.split(".")

        self.execute_js(f'M.Modal.getInstance(document.getElementById("modal-middle-{pkg}-{middle}")).open();')

    def midi_run(self):
        plugins = self.execute_js('$("#plugin-list").val();')
        middles = self.execute_js('$("#middle-list").val();')

    def midi_test(self):
        os.chdir(os.path.join(os.path.split(__file__)[0], ".."))

        port = self.execute_js('$("#rtsv-midi-device").val();')

        self.midi_test_process = multiprocessing.Process(target=midi_play, args=("gui/static/assets/OMR.mid", port))
        self.midi_test_process.daemon = True
        self.midi_test_process.start()

        self("#rtsv-midi-device").setprop("disabled", "disabled")
        self("#rtsv-midi-stop").remove_class("disabled")
        self("#rtsv-midi-test").add_class("disabled")
        self.execute_js("M.AutoInit();")

        self.midi_test_process.join()

        self.execute_js('$("#rtsv-midi-device").removeAttr("disabled")')
        self("#rtsv-midi-stop").add_class("disabled")
        self("#rtsv-midi-test").remove_class("disabled")
        self.execute_js("M.AutoInit();")

    def midi_stop(self):
        self.midi_test_process.terminate()

        self.execute_js('$("#rtsv-midi-device").removeAttr("disabled")')
        self("#rtsv-midi-stop").add_class("disabled")
        self("#rtsv-midi-test").remove_class("disabled")
        self.execute_js("M.AutoInit();")

    def check_rtsv_state(self):
        if self.midi_device_ok and self.server_path_ok:
            self("#rtsv-run-set").show()
            self("#server-status-tips").hide()
        else:
            self("#rtsv-run-set").hide()
            self("#server-status-tips").show()

    def check_rtsv_count(self):
        while self.server_opening.is_set():
            x, y = self.rt_server.valid_info_count, self.rt_server.inval_info_count
            self("#rtsv-midi-recv").inner_text = x + y
            self("#rtsv-midi-valid").inner_text, self("#rtsv-midi-inval").inner_text = x, y

            time.sleep(.5)

    def update_midi_device(self):
        port = self.execute_js('$("#rtsv-midi-device").val();')
        if port:
            self("#midi-device-text").inner_text = port
            self.server_path_ok = True
            self.midi_device_ok = True
        else:
            self("#midi-device-text").inner_text = "N/A"
            self.midi_device_ok = False

        self.check_rtsv_state()

    def run_rt_server(self):
        if isinstance(self.midi_test_process, multiprocessing.Process) and self.midi_test_process.is_alive():
            self.midi_test_process.terminate()

        self("#rtsv-start-btn").fade_out()
        self("#rtsv-midi-pipe").remove_class("red-text")
        self("#rtsv-midi-pipe").inner_text = "连接中"

        try:
            server = self("#server-path-text").inner_text
            port = self("#midi-device-text").inner_text

            self.rt_server = Server(r"D:\Minecraft\Server\paper-243.jar", port)
            self.rt_server_thread = threading.Thread(target=self.rt_server.mainloop)
            self.rt_server_thread.setDaemon(True)
            self.rt_server_thread.start()

            self.server_opening.set()
            server_daemon_thread = threading.Thread(target=self.check_rtsv_count)
            server_daemon_thread.setDaemon(True)
            server_daemon_thread.start()

        except Exception:
            self("#rtsv-midi-pipe").add_class("red-text")
            self("#rtsv-midi-pipe").inner_text = "连接失败"

            self("#rtsv-start-btn").fade_in()
            return

        self("#rtsv-midi-pipe").add_class("green-text")
        self("#rtsv-midi-pipe").inner_text = "已连接"

        self("#rtsv-stop-btn").fade_in()
        self("#mc-path").setprop("disabled", "disabled")
        self("#rtsv-midi-device").setprop("disabled", "disabled")
        self("#rtsv-midi-test").add_class("disabled")
        self.execute_js("M.AutoInit();")

    def term_rt_server(self, force=False):
        if isinstance(self.midi_test_process, multiprocessing.Process) and self.midi_test_process.is_alive():
            self.midi_test_process.terminate()

        self("#rtsv-stop-btn").fade_out()
        self("#rtsv-midi-pipe").remove_class("green-text")
        self("#rtsv-midi-pipe").inner_text = "断开中"

        try:
            self.rt_server.port.panic()
            self.rt_server.port.reset()
            self.rt_server.port.close()
            if os.name == "nt":
                os.system(f'taskkill.exe /F /T /pid:{self.rt_server.pipe._proc.pid}')
            else:
                from signal import SIGTERM, SIGKILL

                os.kill(self.rt_server.pipe._proc.pid, SIGKILL if force else SIGTERM)

            self.server_opening.clear()
        except Exception:
            self("#rtsv-midi-pipe").add_class("red-text")
            self("#rtsv-midi-pipe").inner_text = "断开失败"

            self("#rtsv-stop-btn").fade_in()
            return

        self("#rtsv-midi-pipe").add_class("red-text")
        self("#rtsv-midi-pipe").inner_text = "已断开"

        self("#rtsv-start-btn").fade_in()
        self.execute_js('$("#mc-path").removeAttr("disabled")')
        self.execute_js('$("#rtsv-midi-device").removeAttr("disabled")')
        self("#rtsv-midi-test").remove_class("disabled")
        self.execute_js("M.AutoInit();")


if __name__ == '__main__':
    application = QApplication(sys.argv)
    MainWindow().show()  # The entrance
    application.exit(application.exec_())
