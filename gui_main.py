import logging
import os
import sys

from PyQt5 import QtGui, Qt, QtCore
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QLabel

win = None
ui = None


class CustomLogger(logging.Handler):
    def __init__(self, label: QLabel):
        super().__init__()
        self.label = label

    def emit(self, record):
        try:
            msg = self.format(record)
            print(msg)
            self.label.setText(msg)
        except Exception:
            self.handleError(record)


def browse_midi(checked):
    pth = Qt.QFileDialog.getOpenFileName(win, "请浏览 MIDI 文件路径", '', "MIDI Files (*.midi *.mid)")
    if os.path.exists(pth[0]):
        win.fag_ui.MIDIPathEdit.setPlainText(pth[0])


def browse_dotmc(checked):
    pth = Qt.QFileDialog.getExistingDirectory(win, "请浏览 .minecraft 路径")
    if os.path.exists(pth + '/versions/'):
        win.fag_ui.MCPathEdit.setPlainText(pth)
        win.fag_ui.MCVerBox.clear()
        for dir in os.listdir(pth + '/versions/'):
            win.fag_ui.MCVerBox.addItem(dir)


def refresh_long_note(state):
    if state == QtCore.Qt.Checked:
        win.eap_ui.LongNoteToleranceSpinBox.setEnabled(True)
    else:
        win.eap_ui.LongNoteToleranceSpinBox.setEnabled(False)


def refresh_page(curr):
    if not curr == -1:
        ui.ContentWidget.setCurrentIndex(curr)


def refresh_sequence(curr):
    if not curr == -1:
        win.sq_ui.SequenceWidget.setCurrentIndex(curr)


def add_row(tid, name, inst, combo_func, btn_func):
    row=win.fr_ui.TrackView.model().rowCount()
    model=win.fr_ui.TrackView.model()
    model.insertRow(1)
    model.setItem(row, 0, tid)
    model.setItem(row, 1, name)
    model.setItem(row, 2, inst)
    combo = Qt.QComboBox(win.fr)

    from midi import frontends
    for frontend in frontends.frontend_list:
        combo.addItem(f"{frontend.__name__} ({frontend.__annotations__})")
    combo.currentIndexChanged.connect(combo_func)
    win.fr_ui.TrackView.setIndexWidget(model.index(row, 3), combo)

    btn=Qt.QPushButton(win.fr)
    btn.clicked.connect(btn_func)
    btn.row=row
    win.fr_ui.TrackView.setIndexWidget(model.index(row, 4), btn)


if __name__ == '__main__':
    import MainWindow, FileAndGeneration, Sequence, EffectsAndPerformance, Frontend

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    win = QMainWindow()
    ui = MainWindow.Ui_MainWindow()
    ui.setupUi(win)
    ui.retranslateUi(win)

    logger = logging.getLogger("")
    handler = CustomLogger(ui.LoggingLabel)
    logger.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    win.fag = QWidget(win)
    win.fag_ui = FileAndGeneration.Ui_FileAndGenerationForm()
    win.fag_ui.setupUi(win.fag)
    win.fag_ui.retranslateUi(win.fag)
    win.fag_ui.BrowseMIDIPath.clicked.connect(browse_midi)
    win.fag_ui.BrowseMCPath.clicked.connect(browse_dotmc)
    win.fag_ui.MCVerBox.addItem(" 未指定 .minecraft 目录")
    win.fag_ui.SaveBox.addItem(" 未指定 .minecraft 目录")

    win.sq = QWidget(win)
    win.sq_ui = Sequence.Ui_SequenceForm()
    win.sq_ui.setupUi(win.sq)
    win.sq_ui.retranslateUi(win.sq)
    win.sq_ui.SequenceModeBox.addItem(" 弹性时长（推荐）")
    win.sq_ui.SequenceModeBox.addItem(" 固定刻速率")
    win.sq_ui.SequenceModeBox.addItem(" 固定时长")
    win.sq_ui.SequenceModeBox.currentIndexChanged.connect(refresh_sequence)

    win.eap = QWidget(win)
    win.eap_ui = EffectsAndPerformance.Ui_EffectsAndPerformanceForm()
    win.eap_ui.setupUi(win.eap)
    win.eap_ui.retranslateUi(win.eap)
    win.eap_ui.LongNoteAnalysis.stateChanged.connect(refresh_long_note)

    win.fr=QWidget(win)
    win.fr_ui=Frontend.Ui_FrontendForm()
    win.fr_ui.setupUi(win.fr)
    win.fr_ui.retranslateUi(win.fr)
    win.fr_ui.TrackView.setModel(QtGui.QStandardItemModel(1, 5))
    win.fr_ui.TrackView.setHorizontalHeaderLabels(["音轨序号", "音轨名称", "乐器", "前端", "编辑参数"])

    ui.ContentWidget.addWidget(win.fag)
    ui.ContentWidget.addWidget(win.sq)
    ui.ContentWidget.addWidget(win.eap)
    ui.PageList.addItem("文件与生成")
    ui.PageList.addItem("时序")
    ui.PageList.addItem("效果与性能")
    ui.PageList.addItem("前端")
    ui.PageList.setCurrentRow(0)
    ui.PageList.currentRowChanged.connect(refresh_page)

    win.show()
    sys.exit(app.exec_())
