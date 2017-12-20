import logging
import os

from PyQt5 import QtWidgets, QtCore

from ui.ConfirmInt.ConfirmInterface import ConfirmInterface
from ui.PrefInt.tab import Ui_Form

GROUP = 'PREFERENCE'
TAB = 'GENERAL'
DB = 'db_path'


class PreferenceInterface(QtWidgets.QWidget):
    upt_cfg = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(PreferenceInterface, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.cfg = None

        self.ui.choose_button.clicked.connect(
            lambda: self._dir_path(self.ui.lineEdit))
        self.ui.reset_button.clicked.connect(self.reset_path)

        self.ui.choose_button_2.clicked.connect(
            lambda: self._dir_path(self.ui.lineEdit_2)
        )

        self.ui.buttonBox.rejected.connect(self.close)
        self.ui.buttonBox.accepted.connect(self.close)

        self.ui.lineEdit.textChanged.connect(self._upt_path)
        self.ui.lineEdit_2.textChanged.connect(self._upt_lib_path)

        self.setWindowTitle("Preference")

    def set_config(self, cfg):
        self.cfg = cfg
        self.ui.lineEdit.setText(self.cfg[GROUP][TAB][DB])
        try:
            self.ui.lineEdit_2.setText(self.cfg[GROUP][TAB]['db_lib_path'])
        except KeyError:
            self.ui.lineEdit_2.setText('')

    @staticmethod
    def _dir_path(obj):
        raw_file_name = QtWidgets.QFileDialog.getOpenFileName(
            caption='Open file',
            directory=obj.text() or "/",
            filter="H5 files (*.h5)")
        raw_file_name = str(raw_file_name[0])

        if not raw_file_name:
            return

        obj.setText(raw_file_name)

    def reset_path(self):
        import h5py

        inst = ConfirmInterface()
        inst.setWindowTitle("Attention.")
        inst.set_text(
            r"This will rebuild the data set, and all data will be lost.")
        inst.exec()
        if inst.get_bool():
            dir_name = os.path.join(self.config_path, os.pardir, "lib")
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
            path = os.path.join(dir_name, "lib.h5")
            h5py.File(path, 'w-')
            self._upt_path(path)
        else:
            return

    def _upt_path(self, path):
        """Update the path of library at the line text and config."""
        self.cfg[GROUP][TAB][DB] = path

    def _upt_lib_path(self, path):
        self.cfg[GROUP][TAB]['db_lib_path'] = path

    def closeEvent(self, QCloseEvent):
        self.upt_cfg.emit(self.cfg)
        QCloseEvent.accept()


if __name__ == '__main__':
    import sys

    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    app = QtWidgets.QApplication(sys.argv)
    ins = PreferenceInterface()
    ins.show()
    sys.exit(app.exec_())
