import logging

from PyQt5 import QtWidgets

from ui.ConfirmInt.dialog import Ui_Dialog


class ConfirmInterface(QtWidgets.QDialog):
    """
    This class implement a dialog to confirm some option.
    Its parent should have an attribute 'confirm_info' to print and
    a method to operate if confirmed.
    """

    def __init__(self):
        super(ConfirmInterface, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.bool = False

        self.ui.buttonBox.accepted.connect(self.true)
        self.ui.buttonBox.rejected.connect(self.false)

    def true(self):
        self.bool = True

    def false(self):
        self.bool = False

    def get_bool(self):
        return self.bool

    def set_text(self, text):
        self.ui.label.setText(text)


if __name__ == '__main__':
    import sys

    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    app = QtWidgets.QApplication(sys.argv)
    ins = ConfirmInterface(None)
    ins.show()
    sys.exit(app.exec_())
