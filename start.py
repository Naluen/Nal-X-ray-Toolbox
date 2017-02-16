import logging.config
import os
import sys

from PyQt5 import QtWidgets, QtCore

from ui.GUI import Ui_MainWindow


class ProgramInterface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.report_type = {}
        self.generator_preference_dict = {}
        self.source_sample_set = set()
        self.destination_sample_set = set()

        self.init_list()
        self.ui.checkBox_cleancache.setChecked(1)

        self.ui.pushButton.setStyleSheet(
            "QPushButton{background-color:#16A085;"
            "border:none;color:#ffffff;font-size:20px;}"
            "QPushButton:hover{background-color:#333333;}")
        self.ui.pushButton.clicked.connect(self.handle_button)

        self.ui.listWidget.itemDoubleClicked.connect(self.item_add)
        self.ui.listWidget_2.itemDoubleClicked.connect(self.item_remove)

    def _update_list(self):
        self.ui.listWidget.clear()
        self.ui.listWidget_2.clear()
        source_sample_list = sorted(
            list(
                self.source_sample_set.difference(self.destination_sample_set)
            )
        )
        destination_sample_list = sorted(list(self.destination_sample_set))
        [self.ui.listWidget.addItem(i) for i in list(source_sample_list)]
        [self.ui.listWidget_2.addItem(i) for i in list(destination_sample_list)]

    @QtCore.pyqtSlot()
    def open_parameter_setup(self):
        self.dialogTextBrowser.show()

    def init_list(self):
        parent_directory_dir = r"C:\Users\ang\Dropbox\Experimental_Data"
        xrd_directory = os.path.join(parent_directory_dir, 'SSMBE')
        logging.info("Scanning XRD directory {0}".format(xrd_directory))
        afm_directory = os.path.join(parent_directory_dir, 'AFM')
        logging.info("Scanning XRD directory...")
        [
            self.source_sample_set.add(i) for i in os.listdir(xrd_directory)
            if os.path.isdir(os.path.join(xrd_directory, i))
            ]
        logging.info("Scanning AFM directory...")
        [
            self.source_sample_set.add(i) for i in os.listdir(afm_directory)
            if os.path.isdir(os.path.join(afm_directory, i))
            ]
        source_sample_list = sorted(list(self.source_sample_set))
        [
            self.ui.listWidget.addItem(
                QtWidgets.QListWidgetItem(str(i))) for i in source_sample_list
            ]

    def set_options(self):
        self.report_type['is_xrd'] = self.ui.checkBox_XRD.isChecked()
        self.report_type['is_afm'] = self.ui.checkBox_AFM.isChecked()
        self.report_type['is_rsm'] = self.ui.checkBox_RSM.isChecked()

    def handle_button(self):
        self.set_options()
        destination_sample_list = list(self.destination_sample_set)
        main.makereport(
            destination_sample_list,
            self.report_type,
            is_force=self.ui.checkBox_force.isChecked(),
            is_clear_cache=self.ui.checkBox_cleancache.isChecked(),
            is_show_image=self.ui.checkBox_shImage.isChecked()
        )

    def item_add(self):
        self.destination_sample_set.add(
            self.ui.listWidget.currentItem().text()
        )
        self._update_list()

    def item_remove(self):
        self.destination_sample_set.remove(
            self.ui.listWidget_2.currentItem().text()
        )
        self._update_list()


if __name__ == '__main__':
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    Program = QtWidgets.QApplication(sys.argv)
    MyProgram = ProgramInterface()
    MyProgram.show()
    sys.exit(Program.exec_())
