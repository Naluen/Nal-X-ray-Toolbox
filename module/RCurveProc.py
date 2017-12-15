import logging

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
        self._peak_side_point = []
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
            self._fit,
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

    def _fit(self):
        x = self.data[0, :]
        y = self.data[1, :]

        popt, pcov = curve_fit(pseudo_voigt_func, x, y)
        plt.figure(self.figure.number)
        fun_max = pseudo_voigt_func(0, *popt)
        p = np.abs(pseudo_voigt_func(x, *popt) - fun_max / 2).argsort()[:2]
        fwhm = np.abs(self.data[0, :][p[0]] - self.data[0, :][p[1]])
        step_time = self.attr['_STEPTIME'][0][0]
        step_size = self.attr['_STEP_SIZE'][0][0]
        intensity = fwhm * fun_max * step_time / step_size
        (alpha, gamma, mu) = popt
        plt.plot(
            x,
            pseudo_voigt_func(x, *popt),
            'r-',
            label='fit: \n alpha=%5.3f,\n FWHM=%5.3f,\n maxmium =\
            %5.3f,\n intensity = %5.3f' % (alpha, fwhm, fun_max, intensity),
        )
        plt.legend()
        self.canvas.draw()

    def filter_noise(self):
        b, a = signal.butter(5, 0.1)
        self.data[1, :] = signal.filtfilt(
            b, a, self.data[1, :], method="gust")
        self.refresh_canvas.emit(True)

    def _rm_bk(self, mode='auto'):

        if mode == 'auto':
            rg = 5
            l_p = self.data[0, :][rg]
            r_p = self.data[0, :][-rg]

            def l_func(x_i, l_p_i, r_p_i):
                y_l = self.data[1, :][rg]
                y_r = self.data[1, :][-rg]
                return (y_r - y_l) / (r_p_i - l_p_i) * (x_i - l_p_i) + y_l

            diff = np.asarray([l_func(x, l_p, r_p) for x in self.data[0, :]])

            self.data[1, :] -= diff
            self.data[1, :] -= self.data[1, :].min()
            self.data[0, :] -= self.data[0, :][np.argmax(self.data[1, :])]
            self.refresh_canvas.emit(True)
        elif mode == 'manual':
            self.cid_press = self.canvas.mpl_connect(
                'button_press_event', self._on_press
            )

    def _on_press(self, event):
        x = event.xdata
        self.figure.gca().plot(
            x, self.data[1, :][np.abs(self.data[0, :] - x).argmin()], "*"
        )
        self._peak_side_point.append(x)
        self.canvas.draw()
        if len(self._peak_side_point) == 2:
            l_p = self._peak_side_point[0]
            r_p = self._peak_side_point[1]
            if r_p < l_p:
                l_p, r_p = r_p, l_p
            logging.debug("Selected peak from {0} to {1}".format(l_p, r_p))

            def l_func(x_i, l_p_i, r_p_i):
                y_l = self.data[1, :][np.abs(self.data[0, :] - l_p_i).argmin()]
                y_r = self.data[1, :][np.abs(self.data[0, :] - r_p_i).argmin()]
                return (y_r - y_l) / (r_p_i - l_p_i) * (x_i - l_p_i) + y_l

            diff = np.asarray([l_func(x, l_p, r_p) for x in self.data[0, :]])

            self.data[1, :] -= diff
            self.data[1, :] -= self.data[1, :].min()
            self.data[0, :] -= self.data[0, :][np.argmax(self.data[1, :])]
            self.refresh_canvas.emit(True)

            self.canvas.mpl_disconnect(self.cid_press)
            self._peak_side_point = []

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
