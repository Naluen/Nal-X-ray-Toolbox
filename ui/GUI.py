# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\ang\Dropbox\Programme\PolesFig\ui\GUI.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)

        self.central_widget = QtWidgets.QWidget(MainWindow)
        self.central_widget.setObjectName("central_widget")

        self.groupBox = QtWidgets.QGroupBox(self.central_widget)
        self.groupBox.setGeometry(QtCore.QRect(620, 20, 141, 131))
        self.groupBox.setObjectName("groupBox")

        self.verticalLayoutWidget = QtWidgets.QWidget(self.groupBox)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 20, 111, 91))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.checkBox_XRD = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_XRD.setObjectName("checkBox_XRD")
        self.verticalLayout.addWidget(self.checkBox_XRD)
        self.checkBox_AFM = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_AFM.setObjectName("checkBox_AFM")
        self.verticalLayout.addWidget(self.checkBox_AFM)
        self.checkBox_RSM = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_RSM.setObjectName("checkBox_RSM")
        self.verticalLayout.addWidget(self.checkBox_RSM)

        self.groupBox_2 = QtWidgets.QGroupBox(self.central_widget)
        self.groupBox_2.setGeometry(QtCore.QRect(620, 180, 141, 131))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.groupBox_2)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(10, 20, 111, 91))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBox_force = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_force.setObjectName("checkBox_force")
        self.verticalLayout_2.addWidget(self.checkBox_force)
        self.checkBox_cleancache = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_cleancache.setObjectName("checkBox_cleancache")
        self.verticalLayout_2.addWidget(self.checkBox_cleancache)
        self.checkBox_shImage = QtWidgets.QCheckBox(self.verticalLayoutWidget_2)
        self.checkBox_shImage.setObjectName("checkBox_shImage")
        self.verticalLayout_2.addWidget(self.checkBox_shImage)
        self.pushButton = QtWidgets.QPushButton(self.central_widget)
        self.pushButton.setGeometry(QtCore.QRect(620, 470, 141, 81))

        font = QtGui.QFont()
        font.setPointSize(26)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")

        self.scrollArea = QtWidgets.QScrollArea(self.central_widget)
        self.scrollArea.setGeometry(QtCore.QRect(0, 0, 191, 551))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 189, 549))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.listWidget = QtWidgets.QTreeWidget(self.scrollAreaWidgetContents)
        self.listWidget.setGeometry(QtCore.QRect(0, 0, 191, 551))
        self.listWidget.setObjectName("listWidget")

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.scrollArea_2 = QtWidgets.QScrollArea(self.central_widget)
        self.scrollArea_2.setGeometry(QtCore.QRect(250, 0, 191, 551))
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")

        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 189, 549))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")

        self.listWidget_2 = QtWidgets.QTreeWidget(self.scrollAreaWidgetContents_2)
        self.listWidget_2.setGeometry(QtCore.QRect(0, 0, 191, 551))
        self.listWidget_2.setObjectName("listWidget_2")
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        MainWindow.setCentralWidget(self.central_widget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))

        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionOpen_2 = QtWidgets.QAction(MainWindow)
        self.actionOpen_2.setObjectName("actionOpen_2")
        self.actionParameters = QtWidgets.QAction(MainWindow)
        self.actionParameters.setObjectName("actionParameters")
        self.menuFile.addAction(self.actionOpen_2)
        self.menuEdit.addAction(self.actionParameters)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())

        self.re_translate_ui(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def re_translate_ui(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "Report Type"))
        self.checkBox_XRD.setText(_translate("MainWindow", "XRD"))
        self.checkBox_AFM.setText(_translate("MainWindow", "AFM"))
        self.checkBox_RSM.setText(_translate("MainWindow", "RSM"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Function"))
        self.checkBox_force.setText(_translate("MainWindow", "Force"))
        self.checkBox_cleancache.setText(_translate("MainWindow", "Clean Cache"))
        self.checkBox_shImage.setText(_translate("MainWindow", "Show Image"))
        self.pushButton.setText(_translate("MainWindow", "LaunCH"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.actionOpen_2.setText(_translate("MainWindow", "Open"))
        self.actionParameters.setText(_translate("MainWindow", "Parameters"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
