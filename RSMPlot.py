import logging

import os
from PyQt5 import QtWidgets

from module.OneDScanProc import OneDScanProc
from module.PolesFigureProc import PolesFigureProc
from module.RSMProc import RSMProc
from module.RawFile import RawFile
from module.UxdFile import UxdFile
from module.RCurveProc import RCurveProc

SCAN_DICT = {
    "RSMPlot": RSMProc,
    "PolesFigurePlot": PolesFigureProc,
    "SingleScan": OneDScanProc,
    "RockingCurve": RCurveProc
}
FILE_DICT = {
    ".raw": RawFile,
    ".uxd": UxdFile
}


class UI(object):
    def __init__(self, parent):
        # Main layout.
        self.menu_bar = QtWidgets.QMenuBar(parent)
        self.menu_file = QtWidgets.QMenu("&File", self.menu_bar)
        self.action_open_file = QtWidgets.QAction(
            "Open File...", self.menu_file)
        self.menu_sub_save = QtWidgets.QMenu(
            "Save...", self.menu_file
        )
        self.action_save_main_image = QtWidgets.QAction(
            "Save Main Image...", self.menu_sub_save
        )
        self.action_save_slice_image = QtWidgets.QAction(
            "Save Slice Image...", self.menu_sub_save
        )
        self.action_save_slice_data = QtWidgets.QAction(
            "Save Slice Data...", self.menu_sub_save
        )

        self.menu_sub_save.addAction(self.action_save_main_image)
        self.menu_sub_save.addAction(self.action_save_slice_image)
        self.menu_sub_save.addAction(self.action_save_slice_data)
        self.menu_file.addAction(self.action_open_file)
        self.menu_file.addMenu(self.menu_sub_save)
        self.menu_bar.addMenu(self.menu_file)
        parent.setMenuBar(self.menu_bar)


class ProgramInterface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Right Sub layout with two slice plot
        self.ui = UI(parent=self)
        self.resize(1300, 600)

        self.ui.action_open_file.triggered.connect(self._open_file)

    def _open_file(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open file',
            "/",
            "DATA File (*.raw *.uxd)"
        )
        file_name = str(file_name[0])
        if file_name:
            _, extension = os.path.splitext(file_name)
            opened_file = FILE_DICT[extension]()
            opened_file.get_file(file_name)
            data, attr = opened_file.get_data()
            self.main_scan = SCAN_DICT[attr['TYPE']]()
            self.setCentralWidget(self.main_scan.plot_widget)

            self.main_scan.set_data(data, attr)
            self.main_scan._repaint("")

            self.ui.action_save_main_image.triggered.connect(
                self.main_scan._save_image)


if __name__ == '__main__':
    import sys

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
