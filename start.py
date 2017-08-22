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
        self.attr_ct = 0
        self.show_inter = None
        self.attr_inter = None
        self.active_sender = None
        # Read data sets namespace from h5py library to library tree view.
        self.init_group()
        # Setup report process config.
        self.ui.checkBox_cleancache.setChecked(1)
        # Process button style setup.
        self.ui.pushButton.setStyleSheet(
            "QPushButton{background-color:#16A085;"
            "border:none;color:#ffffff;font-size:20px;}"
            "QPushButton:hover{background-color:#333333;}")
        # Process button for reports.
        self.ui.pushButton.clicked.connect(self.process)
        # Copy Item from library tree view to report tree view.
        self.ui.listWidget.itemDoubleClicked.connect(self.item_add)
        # Remove item from report tree view.
        self.ui.listWidget_2.itemDoubleClicked.connect(self.item_remove)
        # Accept shift and ctrl selection for library tree view
        self.ui.listWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.ContiguousSelection)
        self.ui.listWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        # Accept drag and drop event for library tree view.
        self.setAcceptDrops(True)
        self.ui.listWidget.dragDropOverwriteMode()
        self.ui.listWidget.setAcceptDrops(True)
        # Add right click popup menu for the library tree view
        self.ui.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.listWidget.customContextMenuRequested.connect(self.open_menu)
        # Right popup menu setup.
        self.sub_menu = QtWidgets.QMenu()
        self.sub_menu.addAction(self.ui.plot_action)
        self.sub_menu.addAction(self.ui.attr_action)
        # Connect popup menu with action.
        self.ui.plot_action.triggered.connect(self.trigger_plot)
        self.ui.attr_action.triggered.connect(self.trigger_attr)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                dropped_str = str(url.toLocalFile())
                if os.path.isdir(dropped_str):
                    for path, sub_dirs, files in os.walk(dropped_str):
                        for filename in files:
                            self.read_raw(os.path.join(path, filename))
                elif os.path.isfile(dropped_str):
                    self.save_data(dropped_str)
                else:
                    raise TypeError("Please choose a directory or a file.")
                self.ui.listWidget.clear()
                self.init_group()
        else:
            event.ignore()

    @classmethod
    def save_data(cls, dropped_file):
        # Require data.
        file_handle = h5py.File(cls.data_base_directory(), 'a')

        logging.debug("Reading file {0}...".format(dropped_file))
        instance = Reader.reader(dropped_file)
        if instance is None:
            logging.info('Can not recognize file type.')
            return
        scan_instance = instance.read_data()
        scan_dict = scan_instance.get_scan_dict()

        sub_file_name = (
            scan_dict['sample'] +
            '/' + os.path.basename(dropped_file).split('.')[0])

        logging.debug("Saving file to {0}...".format(sub_file_name))

        group_handle = file_handle.require_group(sub_file_name)

        # Record data.
        data_dict = scan_instance.get_data_dict()
        for key in data_dict.keys():
            try:
                del group_handle[key]
            except (TypeError, KeyError) as e:
                logging.error(e)
                pass
            try:
                group_handle.create_dataset(
                    key,
                    data=data_dict[key]
                )
            except TypeError as e:
                logging.error(e)
                pass

        # Record Setup
        scan_dict = scan_instance.get_scan_dict()
        for key in scan_dict.keys():
            try:
                group_handle.attrs.modify(key, scan_dict[key])
            except TypeError as e:
                logging.error(e)
                pass
        file_handle.close()

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
        file_handle = h5py.File(xrd_lib)

        self.source_sample_set = set([i for i in file_handle.keys()])

        source_sample_list = sorted(list(self.source_sample_set))
        for i in source_sample_list:
            group = QtWidgets.QTreeWidgetItem(self.ui.listWidget, [i])
            for k in file_handle[i].keys():
                QtWidgets.QTreeWidgetItem(group, [k])

        self.view_sort(self.ui.listWidget)

    @classmethod
    def get_list_text(cls, item):
        level = cls.get_tree_level(item)
        if level == 1:
            return [
                cls.data_base_directory(),
                item.parent().text(0) + '/' + item.text(0)
            ]
        elif level == 0:
            return [
                cls.data_base_directory(),
                item.text(0)
            ]
        else:
            return ''

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

    @staticmethod
    def get_tree_level(item):
        level = 0
        while item.parent():
            item = item.parent()
            level += 1

        return level

    def open_menu(self, position):
        self.active_sender = self.sender()
        self.sub_menu.exec_(self.sender().viewport().mapToGlobal(position))

    def trigger_plot(self):
        self.show_inter = PlotInterface(self)
        self.show_inter.show()

    def trigger_attr(self):
        self.attr_ct = 0
        for _ in self.active_sender.selectedItems():
            self.attr_inter = AttrInterface(self)
            self.attr_inter.show()
            self.attr_ct += 1


class PlotInterface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(PlotInterface, self).__init__(parent)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.setCentralWidget(self.canvas)
        self.addToolBar(self.toolbar)
        for i in parent.active_sender.selectedItems():
            Reader.H5File(parent.get_list_text(i)).read_data().plot()
        self.canvas.draw()


class AttrInterface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(AttrInterface, self).__init__(parent)
        self.text = parent.get_list_text(
            parent.active_sender.selectedItems()[parent.attr_ct])

        tab_d = Reader.H5File(self.text).get_scan_dict()

        self.table = QtWidgets.QTableWidget(len(tab_d), 2, self)

        for ind, i in enumerate(tab_d):
            self.table.setItem(ind, 0, QtWidgets.QTableWidgetItem(i))
            self.table.setItem(ind, 1, QtWidgets.QTableWidgetItem(tab_d[i]))

        self.setCentralWidget(self.table)
        self.setWindowTitle(self.text[1])
        self.scan_d = {}
        self.confirm_in = None

    def closeEvent(self, event):
        self.scan_d = {
            self.table.item(i, 0).text(): self.table.item(i, 1).text()
            for i in range(self.table.rowCount())}
        self.confirm_in = ConfirmInterface(self)
        self.confirm_in.show()

        event.accept()


class ConfirmInterface(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ConfirmInterface, self).__init__(parent)

        self.central_widget = QtWidgets.QWidget(parent)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.label = QtWidgets.QLabel(self.central_widget)
        self.label.setText("Would you want to save your change?")
        self.layout.addWidget(self.label)

        self.confirm_button = QtWidgets.QPushButton(self.central_widget)
        self.confirm_button.setText('OK')
        self.layout.addWidget(self.confirm_button)
        self.cancel_button = QtWidgets.QPushButton(self.central_widget)
        self.cancel_button.setText('Cancel')
        self.layout.addWidget(self.cancel_button)

        self.setWindowTitle('')

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.parent = parent
        self.confirm_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.hide)

    def save(self):
        Reader.H5File(
            self.parent.text).set_scan_dict(self.parent.scan_d)

        logging.info('Change saved.')
        self.hide()


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
