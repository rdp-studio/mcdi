import os
import sys

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

from gui.core import HtmlGuiWindow


class OOBEWindow(HtmlGuiWindow):
    def __init__(self, *args, **kwargs):
        super(OOBEWindow, self).__init__(
            "oobe.html", *args, **kwargs
        )

        self.setWindowTitle("Minecraft工具箱 - MCDI")

        self("#wizard-finish").bind("onclick", self.finish)
        self("#wizard-skip").bind("onclick", self.skip)
        self("#wizard-exit").bind("onclick", self.exit)
        self("#mc-path-open").bind("onclick", self.browse_mc_path)

    def finish(self):
        print("Finish.")

    def skip(self):
        pass

    def exit(self):
        os._exit(0)

    def browse_mc_path(self):
        self("#mc-path").value = QFileDialog.getExistingDirectory(self, "浏览.minecraft/ 路径")


if __name__ == '__main__':
    application = QApplication(sys.argv)
    OOBEWindow().show()  # The entrance
    application.exit(application.exec_())
