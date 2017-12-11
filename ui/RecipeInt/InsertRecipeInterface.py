import logging

import numpy
from PyQt5 import QtWidgets, QtCore, QtGui


class InsertRecipeInterface(QtWidgets.QWidget):
    """
    The class provide a interface window to insert the recipe information.
    """
    rcp = QtCore.pyqtSignal(numpy.ndarray)

    def __init__(self):
        """Init."""
        super(InsertRecipeInterface, self).__init__()
        self.mat = []
        self.resize(800, 400)

    def set_mat(self, mat_l):
        self.mat = mat_l

    def set_rcp(self, rcp):
        self.vertical_layout = QtWidgets.QVBoxLayout()

        if rcp is None:
            rcp = numpy.ndarray(shape=(1, 6))
        self.tableWidget = self._na2qtable(rcp)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setHorizontalHeaderLabels(
            ["Composition", "Thickness(nm)", "Temperature(\u2103)", 'Gr(ML/s)',
             'Doping', 'Note'])
        tool_bar = QtWidgets.QToolBar()
        tool_bar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/add.png')),
            "Add new row...",
            lambda: self._new_row(self.tableWidget),
        )
        self.vertical_layout.addWidget(self.tableWidget)
        self.vertical_layout.insertWidget(0, tool_bar)
        self.setLayout(self.vertical_layout)

    def closeEvent(self, event):
        na = self._qtable2na(self.tableWidget)
        if len(na) != 1:
            self.rcp.emit(na)
        event.accept()

    def _del_row(self):
        for i in self.table.selectionModel().selectedRows():
            self.table.removeRow(i.row())

    def _new_row(self, table):
        table.insertRow(table.rowCount())

        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(self.mat)
        combo_box.setCurrentIndex(0)
        table.setCellWidget(table.rowCount() - 1, 0, combo_box)

        combo_box_2 = QtWidgets.QComboBox()
        combo_box_2.addItems(["None", "n", "p"])
        combo_box_2.setCurrentIndex(0)
        table.setCellWidget(table.rowCount() - 1, 4, combo_box_2)

    @staticmethod
    def _qtable2na(q_table):
        """Transform QTable to Numpy Array."""
        q_list = []
        for i in range(q_table.rowCount()):
            for k in range(q_table.columnCount()):
                # If is normal qtable widget item.
                if isinstance(q_table.item(i, k), QtWidgets.QTableWidgetItem):
                    text = q_table.item(i, k).text().encode(encoding='UTF-8')
                    q_list.append(text)
                elif q_table.item(i, k) is None:
                    widget = q_table.cellWidget(i, k)
                    # If is combobox item.
                    try:
                        text = widget.currentIndex()
                        q_list.append(text)
                    except AttributeError:
                        q_list.append(0)
                else:
                    raise TypeError

        na = numpy.asarray(q_list)
        na.reshape(q_table.rowCount(), q_table.columnCount())
        return na

    def _na2qtable(self, na):
        na = numpy.asmatrix(na)
        h, v = na.shape

        q_table = QtWidgets.QTableWidget()
        q_table.setColumnCount(v)
        for i in range(h):
            self._new_row(q_table)

        for i in range(h):
            for k in range(v):
                print(type(q_table.item(i, k)))
                try:
                    widget = q_table.cellWidget(i, k)
                    widget.setCurrentIndex(int(na[i, k]))
                except AttributeError:
                    text = str(na[i, k].decode('utf-8'))
                    q_table.setItem(
                        i, k, QtWidgets.QTableWidgetItem(text)
                    )


        return q_table


if __name__ == '__main__':
    import sys
    import os

    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    app = QtWidgets.QApplication(sys.argv)
    ins = InsertRecipeInterface()
    ins.show()
    sys.exit(app.exec_())
