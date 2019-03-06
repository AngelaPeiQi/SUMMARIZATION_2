# coding: utf-8
import sys, os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType
import codecs
import json
from lib.util.datatype import AttribDict
from lib.util.db import summary2detail, insertDB, exportDB
import traceback
from copy import deepcopy


class ScanSignals(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(AttribDict)
    targetchanged = pyqtSignal(str, str)
    statuschanged = pyqtSignal(bool)
    error = pyqtSignal(tuple)


class ScanWorker(QRunnable):

    def __init__(self, fn, target):
        QThread.__init__(self)

        self.single_scan_target = AttribDict()
        self.single_scan_target.target = target
        self.single_scan_target.plugin = fn
        # self.single_scan_target.result = {}
        self._status = False   # run status
        self.signals = ScanSignals()

    def run(self):
        self.status = True
        try:
            self.single_scan_target.result = self.single_scan_target.plugin(
                self.single_scan_target.target)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(deepcopy(self.single_scan_target))
        finally:
            self.signals.finished.emit()

            # self.status = False


class Document:
    def __init__(self, n, sentence, summarys):
        self.number = n
        self.text = sentence
        self.summary = summarys


def read(path):
    results = []
    for line in codecs.open(path, 'r', 'utf-8'):
        d = json.loads(line)
        i = d['index']
        text = d['text']
        summary = d['summary']
        results.append(Document(i, text, summary))
    return results

current_directory = os.path.dirname(os.path.abspath(__file__))
summ_form, base_class = loadUiType(os.path.join(current_directory, 'mainwindow.ui'))
class MainWindow(QMainWindow, summ_form):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center()) # Center Display
        self._scan_threadpool = QThreadPool()
        model_list = ['Model_1', 'model_2', 'model_3', 'model_4']
        self.comboBox.addItems(model_list)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """训练集打开文件夹，文件路径显示到lineEdit中"""
        fileName1 = QFileDialog.getExistingDirectory(self, "选取文件夹", "./")
        # 设置文件扩展名过滤,注意用双分号间隔
        if fileName1:
            self.lineEdit.setText(fileName1)
            self.lineEdit.setStyleSheet('color: black')
        else:
            self.lineEdit.setText("None")

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """摘要集打开文件，文件路径显示到lineEdit中"""
        fileName1, filetype = QFileDialog.getOpenFileName(self, "选取文件", "./", "All Files (*);;Text Files (*.txt)")
        # 设置文件扩展名过滤,注意用双分号间隔
        if fileName1:
            self.lineEdit_2.setText(fileName1)
            self.lineEdit_2.setStyleSheet('color: black')
        else:
            self.lineEdit_2.setText("None")


    @pyqtSlot()
    def on_startButton_clicked(self):
        """开始预测"""
        test_dir = self.lineEdit.text()
        model_name = self.comboBox.currentText()
        #r = os.system('python main.py')
        r = os.system("python main.py --test_dir %s --model_name %s" % (test_dir, model_name))
        if r == 0:
            self.lineEdit_2.setText("当当当，预测完成喽，快去查看吧！")
            self.lineEdit_2.setStyleSheet('color: blue')
        else:
            self.lineEdit_2.setText("警告，警告，预测出错！")
            self.lineEdit_2.setStyleSheet('color: red')
            print("return: ", r)


    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """展示，文件路径显示到lineEdit中"""
        if self.lineEdit_3.text():
            if self.lineEdit_2.text():
                path = self.lineEdit_2.text()
                summarywork = ScanWorker(read, path)
                summarywork.signals.result.connect(self.onSummaryFinished)
                self._scan_threadpool.start(summarywork)
            else:
                self.lineEdit_2.setText("请选择正确的摘要集!")
                self.lineEdit_2.setStyleSheet('color: red')
                self.textBrowser.setText('')
                self.textBrowser_2.setText('')
        else:
            self.lineEdit_3.setText("请输入正确的ID！")
            self.lineEdit_3.setStyleSheet('color: red')
            self.textBrowser.setText('')
            self.textBrowser_2.setText('')

    def onSummaryFinished(self, results):
        number = self.lineEdit_3.text()
        print(results)

        for doc in results.result:
            if int(number) == int(doc.number):
                text = doc.text.replace(' ', '')
                summ = doc.summary.replace(' ', '')
                self.textBrowser.setText(text)
                self.textBrowser_2.setText(summ)
                break


if __name__ == "__main__":

    app = QApplication(sys.argv)
    scanform = MainWindow()
    scanform.show()
    sys.exit(app.exec_())
