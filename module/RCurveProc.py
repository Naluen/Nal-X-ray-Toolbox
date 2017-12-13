import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from scipy import signal
from scipy.optimize import curve_fit
from scipy.special import wofz

from module.Module import OneDProcModule


def gaussian_func(x, alpha):
    """ Return Gaussian line shape at x with HWHM alpha """
    return np.sqrt(np.log(2) / np.pi) / alpha * np.exp(
        -(x / alpha) ** 2 * np.log(2))


def lorentzian_func(x, gamma):
    """ Return Lorentzian line shape at x with HWHM gamma """
    return gamma / np.pi / (x ** 2 + gamma ** 2)


def voigt_func(x, alpha, gamma):
    """
    Return the Voigt line shape at x with Lorentzian component HWHM
    gamma and Gaussian component HWHM alpha.
    """
    sigma = alpha / np.sqrt(2 * np.log(2))
    wofz_v = np.real(
        wofz(((x - 14.22) + 1j * gamma) / sigma / np.sqrt(2)))

    return wofz_v / sigma / np.sqrt(2 * np.pi)


def pseudo_voigt_func(x, alpha, gamma, mu):
    return mu * gaussian_func(x, alpha) + (
            1 - mu) * lorentzian_func(x, gamma)


class RCurveProc(OneDProcModule):
    def __init__(self):
        super(RCurveProc, self).__init__()
        self.param = {}
        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RockingCurve",

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
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/histogram.png')),
            "Binning data...",
            self._binning_data,
        )
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/noise.png')),
            "Filter noise...",
            self.filter_noise,
        )
        self._toolbar.addAction(
            # QtGui.QIcon(QtGui.QPixmap('icons/noise.png')),
            "Remove DC component...",
            self._rm_bk,
        )
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/curve.png')),
            "Voigt Profile...",
            self._voigt_fit,
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
        if message:
            self.figure.clf()
        plt.figure(self.figure.number)
        plt.plot(
            self.data[0, :],
            self.data[1, :],
            linewidth=1,
            label='data',
        )
        plt.xlabel("{0}".format(self.attr['_STEPPING_DRIVE1']))
        plt.ylabel("{0}".format("Intensity"))
        self.canvas.draw()

    def _voigt_fit(self):
        x = self.data[0, :]
        y = self.data[1, :]

        popt, pcov = curve_fit(pseudo_voigt_func, x, y)
        # f_g = 2 * alpha
        # f_l = 2 * gamma
        # phi = f_l / f_g
        # f_v = f_g * (1 - 2.0056 * 1.0593 + np.sqrt(
        #     phi ** 2 + 2 * 1.0593 * phi + 2.0056 ** 2 * 1.0593 ** 2))
        plt.figure(self.figure.number)
        plt.plot(
            x,
            pseudo_voigt_func(x, *popt),
            'r-',
            # label='fit: alpha=%5.3f, fwhm=%5.3f' % (alpha, 2*alpha),
        )
        plt.legend()
        self.canvas.draw()

    def filter_noise(self):
        b, a = signal.butter(5, 0.1)
        self.data[1, :] = signal.filtfilt(
            b, a, self.data[1, :], method="gust")
        self.refresh_canvas.emit(True)

    def _rm_bk(self):
        # self.data[1, :] = self.data[1, :] - self.data[1, :].min()
        self.data[0, :] = self.data[0, :] - self.data[0, :][
            np.argmax(self.data[1, :])]
        self.data[1, :] = signal.detrend(self.data[1, :], bp=[0, 400, 600])
        self.data[1, :][400:600] = self.data[1, :][400:600] - self.data[1, :][400]
        self.refresh_canvas.emit(True)

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

    # External methods.
    def get_max(self):
        # TODO(azhou@insa-rennes.fr): Use local max instead of max.
        return np.max(self.data[1, :])

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self._repaint(True)

        self.plot_widget.show()

        return self.plot_widget
