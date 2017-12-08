# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\tab.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(491, 409)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("vertical_layout")
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setAccessibleName("")
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.lineEdit = QtWidgets.QLineEdit(self.tab)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout_2.addWidget(self.lineEdit, 1, 0, 1, 1)
        self.choose_button = QtWidgets.QPushButton(self.tab)
        self.choose_button.setObjectName("choose_button")
        self.gridLayout_2.addWidget(self.choose_button, 1, 1, 1, 1)
        self.reset_button = QtWidgets.QPushButton(self.tab)
        self.reset_button.setObjectName("reset_button")
        self.gridLayout_2.addWidget(self.reset_button, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(self.tab)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 4, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.tab)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 2, 0, 1, 1)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridLayout_2.addWidget(self.lineEdit_2, 3, 0, 1, 1)
        self.choose_button_2 = QtWidgets.QPushButton(self.tab)
        self.choose_button_2.setObjectName("choose_button_2")
        self.gridLayout_2.addWidget(self.choose_button_2, 3, 1, 1, 1)
        self.reset_button_2 = QtWidgets.QPushButton(self.tab)
        self.reset_button_2.setObjectName("reset_button_2")
        self.gridLayout_2.addWidget(self.reset_button_2, 3, 2, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(Form)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.choose_button.setText(_translate("Form", "Choose"))
        self.reset_button.setText(_translate("Form", "Reset"))
        self.label.setText(_translate("Form", "Database Location"))
        self.label_2.setText(_translate("Form", "Material Library"))
        self.choose_button_2.setText(_translate("Form", "Choose"))
        self.reset_button_2.setText(_translate("Form", "Reset"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", "General"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())

