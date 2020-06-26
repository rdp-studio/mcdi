import json
import logging
import os
import sys
import re
import threading
import time
from urllib.error import HTTPError
from urllib.request import urlopen
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QLabel
from PyQt5 import QtGui, Qt, QtCore;

class CustomLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.parent = parent

    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
        except Exception:
            self.handleError(record)


if __name__ == '__main__':
    import MainWindow, FileAndGeneration

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app=QApplication(sys.argv)
    win=QMainWindow()
    ui=MainWindow.Ui_MainWindow()
    ui.setupUi(win)
    ui.retranslateUi(win)

    fag=QWidget(win)
    fag_ui=FileAndGeneration.Ui_FileAndGenerationForm()
    fag_ui.setupUi(fag)
    fag_ui.retranslateUi(fag)

    ui.ContentWidget.addWidget(fag)
    ui.PageList.addItem("文件与生成")
    ui.PageList.setCurrentRow(0)

    win.show()
    sys.exit(app.exec_())