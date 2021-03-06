# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\GUI.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(833, 622)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setGeometry(QtCore.QRect(0, 0, 256, 571))
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 833, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuLibrary = QtWidgets.QMenu(self.menubar)
        self.menuLibrary.setObjectName("menuLibrary")
        self.menuModule = QtWidgets.QMenu(self.menubar)
        self.menuModule.setObjectName("menuModule")
        self.menuInstalled_Module = QtWidgets.QMenu(self.menuModule)
        self.menuInstalled_Module.setObjectName("menuInstalled_Module")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionOpen_2 = QtWidgets.QAction(MainWindow)
        self.actionOpen_2.setObjectName("actionOpen_2")
        self.actionParameters = QtWidgets.QAction(MainWindow)
        self.actionParameters.setObjectName("actionParameters")
        self.actionAdd_Module = QtWidgets.QAction(MainWindow)
        self.actionAdd_Module.setObjectName("actionAdd_Module")
        self.actionImport_Data = QtWidgets.QAction(MainWindow)
        self.actionImport_Data.setObjectName("actionImport_Data")
        self.actionExport = QtWidgets.QAction(MainWindow)
        self.actionExport.setObjectName("actionExport")
        self.actionImport = QtWidgets.QAction(MainWindow)
        self.actionImport.setObjectName("actionImport")
        self.actionExport_2 = QtWidgets.QAction(MainWindow)
        self.actionExport_2.setObjectName("actionExport_2")
        self.actionImport_Lib = QtWidgets.QAction(MainWindow)
        self.actionImport_Lib.setObjectName("actionImport_Lib")
        self.actionExport_Lib = QtWidgets.QAction(MainWindow)
        self.actionExport_Lib.setObjectName("actionExport_Lib")
        self.actionDelete = QtWidgets.QAction(MainWindow)
        self.actionDelete.setObjectName("actionDelete")
        self.menuFile.addAction(self.actionOpen_2)
        self.menuFile.addSeparator()
        self.menuEdit.addAction(self.actionParameters)
        self.menuLibrary.addAction(self.actionImport_Data)
        self.menuLibrary.addAction(self.actionDelete)
        self.menuLibrary.addSeparator()
        self.menuLibrary.addAction(self.actionImport_Lib)
        self.menuLibrary.addAction(self.actionExport_Lib)
        self.menuInstalled_Module.addSeparator()
        self.menuModule.addAction(self.actionAdd_Module)
        self.menuModule.addAction(self.menuInstalled_Module.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuLibrary.menuAction())
        self.menubar.addAction(self.menuModule.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuLibrary.setTitle(_translate("MainWindow", "Library"))
        self.menuModule.setTitle(_translate("MainWindow", "Module"))
        self.menuInstalled_Module.setTitle(
            _translate("MainWindow", "Installed Module"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionOpen_2.setText(_translate("MainWindow", "Open"))
        self.actionParameters.setText(_translate("MainWindow", "Parameters"))
        self.actionAdd_Module.setText(_translate("MainWindow", "Add"))
        self.actionImport_Data.setText(_translate("MainWindow", "Import Data"))
        self.actionExport.setText(_translate("MainWindow", "Inport"))
        self.actionImport.setText(_translate("MainWindow", "Import"))
        self.actionExport_2.setText(_translate("MainWindow", "Export"))
        self.actionImport_Lib.setText(_translate("MainWindow", "Import Lib"))
        self.actionExport_Lib.setText(_translate("MainWindow", "Export Lib"))
        self.actionDelete.setText(_translate("MainWindow", "Delete Data"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
