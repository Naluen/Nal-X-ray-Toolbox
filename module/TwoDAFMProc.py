import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)

from module.Module import ProcModule


class TwoDAFMProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(TwoDAFMProc, self).__init__()
        self.param = {"Auto-process": False}
        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "raw_afm",

    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setMinimumHeight(30)

        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/save.png')),
            "Save Image...",
            self._save,
        )
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/settings.png')),
            "Configuration...",
            self._configuration,
        )
        self._toolbar.addSeparator()
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/background.png')),
            "Remove background...",
            self._sub_bk,
        )
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/vertical-alignment.png')),
            "Horizontal align...",
            self._align_rows,
        )

        self.plot_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self._toolbar)
        self.layout.addWidget(self.canvas)
        self.plot_widget.setLayout(self.layout)
        self.plot_widget.closeEvent = self.closeEvent

        self.refresh_canvas.connect(self._repaint)

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message):
        if "Auto-process" in self.param and self.param["Auto-process"]:
            self._sub_bk(False)
            self._align_rows(False)
        ver_max = self.attr['ScanRangeX'].split()
        hor_max = self.attr['ScanRangeY'].split()
        plt.figure(self.figure.number)
        plt.imshow(
            self.data,
            origin='lower',
            extent=[0, float(ver_max[0]), 0, float(hor_max[0])]
        )
        plt.xlabel("X axis({0})".format(ver_max[1]))
        plt.ylabel("Y axis({0})".format(hor_max[1]))
        self.canvas.draw()

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self._repaint("")
        plt.colorbar()

        self.plot_widget.show()

        return self.plot_widget

    def _align_rows(self, repaint=True):
        int_m = self.data
        mask_m = [[np.median(int_m[i])] * len(int_m[0])
                  for i in range(len(int_m))]

        mask_m = np.asanyarray(mask_m)

        self.data = int_m - mask_m
        if repaint:
            self.refresh_canvas.emit(True)

    def _sub_bk(self, repaint=True):
        import scipy.linalg
        int_m = self.data
        x, y = int_m.shape
        # regular grid covering the domain of the data
        x, y = np.meshgrid(np.arange(0, int(x), 1),
                           np.arange(0, int(y), 1))
        xx = x.flatten()
        yy = y.flatten()
        data = np.c_[xx, yy, int_m.flatten()]

        order = 2  # 1: linear, 2: quadratic
        if order == 1:
            # best-fit linear plane
            A = np.c_[data[:, 0], data[:, 1], np.ones(data.shape[0])]
            C, _, _, _ = scipy.linalg.lstsq(A, data[:, 2])  # coefficients

            Z = np.dot(
                np.c_[xx, yy, np.ones(xx.shape)], C).reshape(int_m.shape)

        elif order == 2:
            # best-fit quadratic curve
            A = np.c_[
                np.ones(data.shape[0]),
                data[:, :2],
                np.prod(data[:, :2], axis=1),
                data[:, :2] ** 2]
            C, _, _, _ = scipy.linalg.lstsq(A, data[:, 2])

            # evaluate it on a grid
            Z = np.dot(
                np.c_[np.ones(xx.shape), xx, yy, xx * yy, xx ** 2, yy ** 2],
                C).reshape(int_m.shape)
        else:
            return

        # return int_m - Z
        self.data = int_m - Z
        if repaint:
            self.refresh_canvas.emit(True)


    def _configuration(self):
        widget = self._build_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(widget, "TwoD AFM")
        self.q_tab_widget.closeEvent = self._configuration_close
        self.q_tab_widget.show()

    def closeEvent(self, event):
        self.attr.update(self.param)
        self.send_param.emit(dict(self.attr))
