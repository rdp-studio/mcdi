import importlib
import os
import sys
import uuid
import webbrowser

from PyQt5.QtWidgets import QApplication, QFileDialog

from gui.core import HtmlGuiWindow

sys.path.append("..")


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

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(
            "main.html", *args, **kwargs
        )

        self.setWindowTitle("Minecraft工具箱 - MCDI")

        self("#about-l1").bind("onclick", lambda: webbrowser.open(self.GITHUB_URL))
        self("#about-l2").bind("onclick", lambda: webbrowser.open(self.BILIBILI_URL))
        self("#about-l3").bind("onclick", lambda: webbrowser.open(self.FRIEND_URL))
        self("#midi-path").bind("ondblclick", self.browse_midi_path)
        self("#plugin-chk-btn").bind("onclick", self.reload_plugin_cfg)
        self("#plugin-cfg-btn").bind("onclick", self.open_plugin_cfg)
        self("#middle-chk-btn").bind("onclick", self.reload_middle_cfg)
        self("#middle-cfg-btn").bind("onclick", self.open_middle_cfg)
        self(".fixed-action-btn").bind("onclick", self.load_objects)

        self.plugins = {}
        self.middles = {}

        self.objects_loaded = False

        os.chdir("..")

    def browse_midi_path(self):
        self("#midi-path").value = QFileDialog.getOpenFileUrl(self, "浏览MIDI路径")[0].toString().strip("file:///")

    def load_objects(self):
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

                if isinstance(middle, type) and issubclass(middle, Plugin) and middle is not Middle:
                    middle[pkg].append({
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

        self.execute_js("M.AutoInit();")

        self.plugins.update(plugins)
        self.middles.update(middles)

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


if __name__ == '__main__':
    application = QApplication(sys.argv)
    MainWindow().show()  # The entrance
    application.exit(application.exec_())
