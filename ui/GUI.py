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
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.horizontalLayout.addWidget(self.treeWidget)
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
        self.menuPlot = QtWidgets.QMenu(self.menubar)
        self.menuPlot.setObjectName("menuPlot")
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
        self.actionDelete_Data = QtWidgets.QAction(MainWindow)
        self.actionDelete_Data.setObjectName("actionDelete_Data")
        self.actionRename = QtWidgets.QAction(MainWindow)
        self.actionRename.setObjectName("actionRename")
        self.actionCut = QtWidgets.QAction(MainWindow)
        self.actionCut.setObjectName("actionCut")
        self.actionCopy = QtWidgets.QAction(MainWindow)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtWidgets.QAction(MainWindow)
        self.actionPaste.setObjectName("actionPaste")
        self.action_Detail = QtWidgets.QAction(MainWindow)
        self.action_Detail.setObjectName("action_Detail")
        self.action_Plot = QtWidgets.QAction(MainWindow)
        self.action_Plot.setObjectName("action_Plot")
        self.actionInsert_Recipe = QtWidgets.QAction(MainWindow)
        self.actionInsert_Recipe.setObjectName("actionInsert_Recipe")
        self.actionAdd_Group = QtWidgets.QAction(MainWindow)
        self.actionAdd_Group.setObjectName("actionAdd_Group")
        self.menuFile.addAction(self.actionOpen_2)
        self.menuFile.addSeparator()
        self.menuEdit.addAction(self.actionParameters)
        self.menuLibrary.addAction(self.actionImport_Data)
        self.menuLibrary.addAction(self.actionAdd_Group)
        self.menuLibrary.addAction(self.actionCut)
        self.menuLibrary.addAction(self.actionCopy)
        self.menuLibrary.addAction(self.actionDelete_Data)
        self.menuLibrary.addAction(self.action_Detail)
        self.menuLibrary.addAction(self.actionRename)
        self.menuLibrary.addAction(self.actionPaste)
        self.menuLibrary.addSeparator()
        self.menuLibrary.addAction(self.actionImport_Lib)
        self.menuLibrary.addAction(self.actionExport_Lib)
        self.menuLibrary.addSeparator()
        self.menuLibrary.addAction(self.actionInsert_Recipe)
        self.menuInstalled_Module.addSeparator()
        self.menuModule.addAction(self.actionAdd_Module)
        self.menuModule.addAction(self.menuInstalled_Module.menuAction())
        self.menuPlot.addAction(self.action_Plot)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuLibrary.menuAction())
        self.menubar.addAction(self.menuPlot.menuAction())
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
        self.menuPlot.setTitle(_translate("MainWindow", "Plot"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionOpen_2.setText(_translate("MainWindow", "Open"))
        self.actionParameters.setText(_translate("MainWindow", "Parameters"))
        self.actionAdd_Module.setText(_translate("MainWindow", "Add"))
        self.actionImport_Data.setText(_translate("MainWindow", "&Add Data"))
        self.actionImport_Data.setShortcut(_translate("MainWindow", "Alt+A"))
        self.actionExport.setText(_translate("MainWindow", "Inport"))
        self.actionImport.setText(_translate("MainWindow", "Import"))
        self.actionExport_2.setText(_translate("MainWindow", "Export"))
        self.actionImport_Lib.setText(_translate("MainWindow", "Import Lib"))
        self.actionImport_Lib.setShortcut(
            _translate("MainWindow", "Ctrl+Alt+Ins"))
        self.actionExport_Lib.setText(_translate("MainWindow", "Export Lib"))
        self.actionDelete_Data.setText(_translate("MainWindow", "Delete"))
        self.actionDelete_Data.setShortcut(_translate("MainWindow", "Del"))
        self.actionRename.setText(_translate("MainWindow", "&Rename"))
        self.actionRename.setShortcut(_translate("MainWindow", "Alt+R"))
        self.actionCut.setText(_translate("MainWindow", "Cut"))
        self.actionCut.setShortcut(_translate("MainWindow", "Alt+X"))
        self.actionCopy.setText(_translate("MainWindow", "&Copy"))
        self.actionCopy.setShortcut(_translate("MainWindow", "Alt+C"))
        self.actionPaste.setText(_translate("MainWindow", "&Paste"))
        self.actionPaste.setShortcut(_translate("MainWindow", "Alt+P"))
        self.action_Detail.setText(_translate("MainWindow", "&Detail"))
        self.action_Detail.setShortcut(_translate("MainWindow", "Alt+D"))
        self.action_Plot.setText(_translate("MainWindow", "&Plot"))
        self.action_Plot.setShortcut(_translate("MainWindow", "Alt+P"))
        self.actionInsert_Recipe.setText(_translate("MainWindow", "Recipe"))
        self.actionInsert_Recipe.setToolTip(_translate("MainWindow", "Recipe"))
        self.actionInsert_Recipe.setShortcut(
            _translate("MainWindow", "Ctrl+Alt+Shift+R"))
        self.actionAdd_Group.setText(_translate("MainWindow", "Add Group"))
        self.actionAdd_Group.setShortcut(
            _translate("MainWindow", "Ctrl+Alt+Shift+A"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
