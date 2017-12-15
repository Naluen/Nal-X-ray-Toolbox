import logging

from PyQt5 import QtWidgets, QtCore

from ui.TableInt.table import Ui_Form
from ui.ConfirmInt.ConfirmInterface import ConfirmInterface
import numpy as np
from distutils import util


class TableInt(QtWidgets.QWidget):
    proc_done = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(TableInt, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.is_item_changed = False

    def dict2table(self, dct):
        if isinstance(dct, dict):
            self.ui.tableWidget.setColumnCount(2)
            self.ui.tableWidget.setRowCount(len(dct))
            self.ui.tableWidget.setHorizontalHeaderLabels(["Key", "Value"])
            self.ui.tableWidget.verticalHeader().hide()
            sorted_keys = sorted(dct.keys(), key=lambda x: x[0])
            i = 0
            for key in sorted_keys:
                key_item = QtWidgets.QTableWidgetItem(str(key))
                key_item.setFlags(key_item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.ui.tableWidget.setItem(i, 0, key_item)
                self.ui.tableWidget.setItem(
                    i, 1, QtWidgets.QTableWidgetItem(str(dct[key]))
                )
                if isinstance(dct[key], np.ndarray):
                    self.ui.tableWidget.item(i, 1).setFlags(
                        key_item.flags() & ~QtCore.Qt.ItemIsEditable)
                i += 1

            self.ui.tableWidget.resizeColumnsToContents()
            self.ui.tableWidget.resizeRowsToContents()

            self.ui.tableWidget.itemChanged.connect(self.item_changed)
            self.dct = dct
        else:
            raise TypeError

    def item_changed(self):
        self.is_item_changed = True

    def table2dict(self):
        scan_d = {
            self.ui.tableWidget.item(i, 0).text():
                self.ui.tableWidget.item(i, 1).text()
            for i in range(self.ui.tableWidget.rowCount())
        }
        for i in scan_d:
            if i in self.dct:
                if isinstance(self.dct[i], (bool, np.bool_)):
                    scan_d[i] = util.strtobool(scan_d[i])
                elif isinstance(self.dct[i], (np.int_, int)):
                    scan_d[i] = np.int(scan_d[i])
                elif isinstance(self.dct[i], (np.float_, float)):
                    scan_d[i] = np.float(scan_d[i])
        return scan_d

    def closeEvent(self, event):
        if self.is_item_changed:
            self.confirm_in = ConfirmInterface()
            self.confirm_in.set_text("Would you want to save your changes?")
            self.confirm_in.setWindowModality(QtCore.Qt.WindowModal)
            self.confirm_in.exec()

            if self.confirm_in.get_bool():
                self.proc_done.emit(self.table2dict())
        event.accept()


if __name__ == '__main__':
    import sys

    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    app = QtWidgets.QApplication(sys.argv)
    ins = TableInt()
    ins.show()
    sys.exit(app.exec_())
