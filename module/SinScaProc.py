import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)

from module.Module import ProcModule


class SinScaProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(SinScaProc, self).__init__()
        self.param = {}
        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "SingleScan",

    # Build Canvas
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

        self.plot_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self._toolbar)
        self.layout.addWidget(self.canvas)
        self.plot_widget.setLayout(self.layout)
        self.plot_widget.closeEvent = self.closeEvent

        self.refresh_canvas.connect(self._repaint)

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message):
        plt.figure(self.figure.number)
        plt.plot(
            self.data[0, :],
            self.data[1, :],
            linewidth=1
        )
        plt.xlabel("{0}".format(self.attr['_STEPPING_DRIVE1']))
        plt.ylabel("{0}".format("Intensity"))
        self.canvas.draw()

    # Config Menu.
    def _configuration(self):
        widget = self._build_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(widget, self.attr['Type'])
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _close_configuration(self, event):
        self.refresh_canvas.emit(True)
        event.accept()

    # Externel methods.
    def get_max(self):
        # TODO(azhou@insa-rennes.fr): Use local max instead of max.
        return np.max(self.data[1, :])

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self._repaint(True)

        self.plot_widget.show()

        return self.plot_widget
