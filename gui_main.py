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
from PyQt5 import QtGui, Qt, QtCore

win=None
ui=None


class CustomLogger(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
        except Exception:
            self.handleError(record)


def refresh_page(curr):
    if not curr==-1:
        ui.ContentWidget.setCurrentIndex(curr)


if __name__ == '__main__':
    import MainWindow, FileAndGeneration, Sequence

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    win = QMainWindow()
    ui = MainWindow.Ui_MainWindow()
    ui.setupUi(win)
    ui.retranslateUi(win)

    win.fag = QWidget(win)
    win.fag_ui = FileAndGeneration.Ui_FileAndGenerationForm()
    win.fag_ui.setupUi(win.fag)
    win.fag_ui.retranslateUi(win.fag)

    win.sq = QWidget(win)
    win.sq_ui = Sequence.Ui_SequenceForm()
    win.sq_ui.setupUi(win.sq)
    win.sq_ui.retranslateUi(win.sq)

    ui.ContentWidget.addWidget(win.fag)
    ui.ContentWidget.addWidget(win.sq)
    ui.PageList.addItem("文件与生成")
    ui.PageList.addItem("时序")
    ui.PageList.setCurrentRow(0)
    ui.PageList.currentRowChanged.connect(refresh_page)

    win.show()
    sys.exit(app.exec_())
