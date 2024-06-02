import os
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QFileDialog, QDialog, QTextEdit
from PyQt5.QtCore import Qt

import analyzer


class ChordsWindow(QDialog):
    def __init__(self, chords):
        super().__init__()
        self.setWindowTitle("和弦列表")
        self.resize(1200, 800)
        layout = QVBoxLayout()
        self.textEdit = QTextEdit()
        self.textEdit.setPlainText(chords)
        self.textEdit.setReadOnly(True)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

class FileDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('拖拽歌曲至窗口')
        self.setGeometry(300, 300, 1200, 800)

        layout = QVBoxLayout()

        # 设置窗口背景颜色
        self.setStyleSheet("background-color: lightblue;")

        # Table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["名称", "调性", "BPM", "和弦"])
        layout.addWidget(self.tableWidget)

        # 设置栏目自适应窗口大小
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # "File Name" 列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Export Button
        self.exportButton = QPushButton("生成表格")
        self.exportButton.clicked.connect(self.exportToCSV)
        layout.addWidget(self.exportButton)

        # Clear Button
        self.clearButton = QPushButton("清空")
        self.clearButton.clicked.connect(self.clearTable)
        layout.addWidget(self.clearButton)

        self.setLayout(layout)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.addFileDetailsToTable(file_path)

    def addFileDetailsToTable(self, file_path):
        file_name = os.path.basename(file_path)
        tonality, global_bpm, chords_list = analyzer.process(file_path) # main process

        chords = ', '.join(chords_list)
        if global_bpm < 120:
            temp = 2 * global_bpm
            global_bpm = str(global_bpm) + ' or ' + str(temp)
        else:
            global_bpm = str(global_bpm)

        row_count = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_count)
        self.tableWidget.setItem(row_count, 0, QTableWidgetItem(file_name))
        self.tableWidget.setItem(row_count, 1, QTableWidgetItem(tonality))
        self.tableWidget.setItem(row_count, 2, QTableWidgetItem(global_bpm))

        show_chords_button = QPushButton("显示和弦")
        show_chords_button.clicked.connect(lambda state, chords=chords: self.showChords(chords))
        self.tableWidget.setCellWidget(row_count, 3, show_chords_button)

    def showChords(self, chords):
        chords_window = ChordsWindow(chords)
        chords_window.exec_()

    def clearTable(self):
        self.tableWidget.setRowCount(0)

    def exportToCSV(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)")

        if file_path:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(["名称", "调性", "BPM"])

                for row in range(self.tableWidget.rowCount()):
                    row_data = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    writer.writerow(row_data)


if __name__ == '__main__':
    app = QApplication([])
    window = FileDropWidget()
    window.show()
    app.exec_()
