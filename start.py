import logging.config
import os
import sys

import h5py
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar
)

from XrdAnalysis import Reader
from XrdAnalysis import ReportGenerator
from ui.GUI import Ui_MainWindow


class ProgramInterface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow(self)

        self.report_type = {}
        self.generator_preference_dict = {}
        self.source_sample_set = set()
        self.destination_sample_set = set()
        self.current_item = []
        self.show_inter = None
        self.attr_inter = None

        self.init_group()
        self.ui.checkBox_cleancache.setChecked(1)

        self.ui.pushButton.setStyleSheet(
            "QPushButton{background-color:#16A085;"
            "border:none;color:#ffffff;font-size:20px;}"
            "QPushButton:hover{background-color:#333333;}")

        self.ui.pushButton.clicked.connect(self.process)
        self.ui.listWidget.itemDoubleClicked.connect(self.item_add)
        self.ui.listWidget_2.itemDoubleClicked.connect(self.item_remove)

        self.ui.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.listWidget_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.open_menu)
        self.ui.listWidget_2.customContextMenuRequested.connect(self.open_menu)

        self.sub_menu = QtWidgets.QMenu()
        self.sub_menu.addAction(self.ui.plot_action)
        self.sub_menu.addAction(self.ui.attr_action)

        self.ui.plot_action.triggered.connect(self.trigger_plot)
        self.ui.attr_action.triggered.connect(self.trigger_attr)

    @staticmethod
    def view_sort(view):
        view.sortItems(0, QtCore.Qt.AscendingOrder)
        root = view.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item.sortChildren(0, QtCore.Qt.AscendingOrder)
            if item.childCount() == 0:
                view.takeTopLevelItem(i)

    @QtCore.pyqtSlot()
    def open_parameter_setup(self):
        self.dialogTextBrowser.show()

    @staticmethod
    def data_base_directory():
        import os
        if os.name is 'nt':
            xrd_lib = r"C:\Users\hang\Dropbox\Experimental_Data\xrd_lib.h5"
        else:
            xrd_lib = r"/Users/zhouang/Dropbox/Experimental_Data/xrd_lib.h5"
        return xrd_lib

    def init_group(self):
        xrd_lib = self.data_base_directory()
        with open(xrd_lib, 'r') as fp:
            file_handle = h5py.File(xrd_lib)

        self.source_sample_set = set([i for i in file_handle.keys()])

        source_sample_list = sorted(list(self.source_sample_set))
        for i in source_sample_list:
            group = QtWidgets.QTreeWidgetItem(self.ui.listWidget, [i])
            for k in file_handle[i].keys():
                QtWidgets.QTreeWidgetItem(group, [k])

        self.view_sort(self.ui.listWidget)

    def item_add(self):
        text = self.ui.listWidget.currentItem().text(0)
        if self.ui.listWidget.currentItem().parent() is not None:
            # If the item is not in top level.
            text2 = self.ui.listWidget.currentItem().parent().text(0)
            # Get current item text.
            gp = self.ui.listWidget_2.findItems(
                text2, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)
            # Find if parent item exist.
            if not gp:
                gp = [QtWidgets.QTreeWidgetItem(self.ui.listWidget_2, [text2])]

            QtWidgets.QTreeWidgetItem(gp[0], [text])

        self.ui.listWidget_2.update()
        self.view_sort(self.ui.listWidget)
        self.view_sort(self.ui.listWidget_2)

    def item_remove(self):
        item = self.ui.listWidget_2.currentItem()
        if item.parent() is not None:
            item.parent().takeChild(item.parent().indexOfChild(item))
        else:
            self.ui.listWidget_2.takeTopLevelItem(
                self.ui.listWidget_2.indexOfTopLevelItem(item))

        self.view_sort(self.ui.listWidget_2)

    def process(self):
        file_list = []
        root = self.ui.listWidget_2.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            for k in range(item.childCount()):
                chd = item.child(k)
                file_list.append(item.text(0) + '/' + chd.text(0))

        file_list = [[self.data_base_directory(), i] for i in file_list]

        logging.debug(file_list)

        pdf_file_name = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save Report file',
            'report',
            "PDF files (*.pdf)")
        pdf_file_name = str(pdf_file_name[0])

        if pdf_file_name:
            os.chdir(os.path.dirname(pdf_file_name))
            report = ReportGenerator.Generator()
            report.print_to_pdf(file_list, file_name=pdf_file_name)
        else:
            return

    def open_menu(self, position):
        indexes = self.sender().selectedIndexes()

        if len(indexes) > 0:
            level = 0
            index = indexes[0]

            while index.parent().isValid():
                index = index.parent()
                level += 1
        else:
            return

        if level == 1:
            self.current_item = [
                self.data_base_directory(),
                self.sender().currentItem().parent().text(0) + '/' +
                self.sender().currentItem().text(0)
            ]
            self.sub_menu.exec_(self.sender().viewport().mapToGlobal(position))

    def trigger_plot(self):
        self.show_inter = PlotInterface(self)
        self.show_inter.show()

    def trigger_attr(self):
        self.attr_inter = AttrInterface(self)
        self.attr_inter.show()


class PlotInterface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PlotInterface, self).__init__(parent)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setCentralWidget(self.canvas)
        self.addToolBar(self.toolbar)
        Reader.H5File(parent.current_item).read_data().plot()
        self.canvas.draw()


class AttrInterface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AttrInterface, self).__init__(parent)

        tab_d = Reader.H5File(parent.current_item).read_data().get_scan_dict()
        self.table = QtWidgets.QTableWidget(len(tab_d), 2, self)
        for ind, i in enumerate(tab_d):
            self.table.setItem(ind, 0, QtWidgets.QTableWidgetItem(i))
            self.table.setItem(ind, 1, QtWidgets.QTableWidgetItem(tab_d[i]))
        self.setCentralWidget(self.table)


if __name__ == '__main__':
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    Program = QtWidgets.QApplication(sys.argv)
    MyProgram = ProgramInterface()
    MyProgram.show()
    sys.exit(Program.exec_())
