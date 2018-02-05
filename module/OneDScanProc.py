import abc
import logging
import os
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas

from module.Module import BasicToolBar
from module.Module import ProcModule


class OneDScanProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self._peak_side_point = []

        self.param = {
            "disable_log_y": False
        }
        self.figure = plt.figure()
        self._build_plot_widget()

    @property
    def name(self):
        return "OneDScanProc"

    @property
    @abc.abstractmethod
    def supp_type(self):
        return "SingleScan"

    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._toolbar = BasicToolBar(self)
        # Fit tool button
        fit_tool_button = QtWidgets.QToolButton()

        pseudo_voigt_fit_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/curve.png')),
            "Fit with (pseudo voigt)...",
            fit_tool_button
        )
        pseudo_voigt_fit_action.triggered.connect(
            lambda: self._fit(fit_fun='pseudo voigt')
        )
        fit_tool_button.setDefaultAction(
            pseudo_voigt_fit_action
        )

        fit_tool_button_menu = QtWidgets.QMenu()
        for i in self.fun_dict:
            fit_tool_button_menu.addAction(
                i,
                lambda: self._fit(fit_fun=i)
            )
        fit_tool_button.setMenu(fit_tool_button_menu)
        self._toolbar.addWidget(fit_tool_button)

        self.plot_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self._toolbar)
        self.layout.addWidget(self.canvas)
        self.plot_widget.setLayout(self.layout)
        self.plot_widget.closeEvent = self.closeEvent

        self.refresh_canvas.connect(self._repaint)

    def _build_config_widget(self):
        config_widget = QtWidgets.QWidget(self.plot_widget)
        config_layout = QtWidgets.QVBoxLayout()
        config_widget.setLayout(config_layout)

        disable_log_plot_q_ratio_button = QtWidgets.QRadioButton(
            "Disable Y-Log Plot")
        disable_log_plot_q_ratio_button.setChecked(self.param["disable_log_y"])
        disable_log_plot_q_ratio_button.toggled.connect(
            partial(self._upt_param, "disable_log_y"))
        config_layout.addWidget(disable_log_plot_q_ratio_button)

        return config_widget

    def _configuration(self):
        widget = self._build_config_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        try:
            self.q_tab_widget.addTab(widget, self.attr['Type'])
        except KeyError:
            self.q_tab_widget.addTab(widget, 'CONFIG')

        self.q_tab_widget.closeEvent = self._configuration_close
        self.q_tab_widget.show()

    def _configuration_close(self, event):
        self._repaint(True)
        event.accept()

    def _export_data(self):
        if not hasattr(self, 'data'):
            return

        data_file_name = QtWidgets.QFileDialog.getSaveFileName(
            self.plot_widget,
            'Save Image file',
            "/",
            "Txt File (*.txt)"
        )
        data_file_name = data_file_name[0]
        if not data_file_name:
            return
        with open(data_file_name, 'w') as file_handle:
            file_handle.write(
                "%s, intensity" % self.attr['_STEPPING_DRIVE1'] + os.linesep)
            for i, k in zip(self.data[0], self.data[1]):
                file_handle.write("{0}, {1}".format(i, k) + os.linesep)

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message=True):
        logging.debug("Re-Paint Main Image")
        plt.figure(self.figure.number)
        if message:
            self.figure.clf()
        if 'disable_log_y' in self.param and self.param['disable_log_y']:
            plt.plot(
                self.data[0, :],
                self.data[1, :],
                linewidth=1,
                color='C2',
            )
        else:
            plt.semilogy(
                self.data[0, :],
                self.data[1, :],
                linewidth=1,
                color='C2',
            )
        plt.xlabel("{0}".format(self.attr['STEPPING_DRIVE1']))
        plt.ylabel("{0}".format("Intensity"))
        self.canvas.draw()

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self._repaint(True)

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr, *args, **kwargs):
        x = data[0, :][~np.isnan(data[1, :])]
        y = data[1, :][~np.isnan(data[1, :])]
        self.data = np.vstack((x, y))
        self.attr = attr

        return self

    @property
    def fun_dict(self):
        return {
            'pseudo voigt': self.pseudo_voigt_func,
            'voigt': self.voigt_func,
            'lorentz': self.lorentzian_func,
            'gaussian': self.gaussian_func,
        }

    @staticmethod
    def gaussian_func(x, alpha, x0=0):
        """ Return Gaussian line shape at x with HWHM alpha """
        return np.sqrt(np.log(2) / np.pi) / alpha * np.exp(
            -((x - x0) / alpha) ** 2 * np.log(2))

    @staticmethod
    def lorentzian_func(x, gamma, x0=0):
        """ Return Lorentzian line shape at x with HWHM gamma """
        return gamma / np.pi / ((x - x0) ** 2 + gamma ** 2)

    @staticmethod
    def voigt_func(x, alpha, gamma, x0=0):
        from scipy.special._ufuncs import wofz
        """
        Return the Voigt line shape at x with Lorentzian component HWHM
        gamma and Gaussian component HWHM alpha.
        """
        sigma = alpha / np.sqrt(2 * np.log(2))
        wofz_v = np.real(
            wofz((((x - x0) - 14.22) + 1j * gamma) / sigma / np.sqrt(2)))

        return wofz_v / sigma / np.sqrt(2 * np.pi)

    @staticmethod
    def pseudo_voigt_func(x, alpha, gamma, mu, x0=0):
        def gaussian_func(x, alpha):
            """ Return Gaussian line shape at x with HWHM alpha """
            return np.sqrt(np.log(2) / np.pi) / alpha * np.exp(
                -(x / alpha) ** 2 * np.log(2))

        def lorentzian_func(x, gamma):
            """ Return Lorentzian line shape at x with HWHM gamma """
            return gamma / np.pi / (x ** 2 + gamma ** 2)

        return mu * gaussian_func(x - x0, alpha) + (
                1 - mu) * lorentzian_func(x - x0, gamma)

    def _binning_data(self, bin_width=5):
        from scipy.stats import binned_statistic

        y, _, _ = binned_statistic(
            self.data[0, :],
            self.data[1, :],
            statistic='median',
            bins=int(np.floor(len(self.data[1, :]) / bin_width))
        )
        x = self.data[0, :][::bin_width]
        f = lambda a, b: (
                                 len(a) > len(b) and (a[:len(b)], b)
                         ) or (a, b[:len(a)])
        (x, y) = f(x, y)
        self.data = np.vstack((x, y))
        self._repaint(True)

    def _fit(self, fit_fun='pseudo voigt', is_plot=True):
        """
        Fit the y data with selected function and plot.
        :return:
        """
        from scipy.optimize import curve_fit
        from functools import partial
        if not hasattr(self, 'data'):
            return

        x = self.data[0, :]
        y = self.data[1, :]

        fit_fun = self.fun_dict[fit_fun]
        x0 = self._x_shift_to_centre()
        fit_fun = partial(fit_fun, x0=x0)
        logging.debug("X shift value is %s" % -x0)

        popt, pcov = curve_fit(fit_fun, x, y)
        plt.figure(self.figure.number)

        fun_max = fit_fun(0, *popt)
        p = np.abs(fit_fun(x, *popt) - fun_max / 2).argsort()[:2]
        fwhm = np.abs(self.data[0, :][p[0]] - self.data[0, :][p[1]])
        extra_res = (fun_max, fwhm)

        if is_plot:
            plt.figure(self.figure.number)
            if 'disable_log_y' in self.param and self.param['disable_log_y']:
                plt.plot(
                    x,
                    fit_fun(x, *popt),
                    linewidth=1,
                    color='C3',
                )
            else:
                self.figure.axes[0].semilogy(
                    x,
                    fit_fun(x, *popt),
                    linewidth=1,
                    color='C1',
                )
            self.canvas.draw()

        self._recent_fit_res = extra_res

        return x, fit_fun(x, *popt), extra_res

    def _filter(self):
        logging.debug("Butter Filter...")
        from scipy import signal
        arg = signal.butter(5, 0.1)
        self.data[1, :] = signal.filtfilt(
            *arg, self.data[1, :], method="gust")
        self.refresh_canvas.emit(True)

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

    def _x_shift_to_centre(self):
        return self.data[0, :][np.argmax(self.data[1, :])]

    def _target(self, mode='auto', is_plot=True):

        if mode == 'auto':
            rg = 50
            l_p = self.data[0, :][rg]
            r_p = self.data[0, :][-rg]

            def l_func(x_i, l_p_i, r_p_i):
                y_l = self.data[1, :][rg]
                y_r = self.data[1, :][-rg]
                return (y_r - y_l) / (r_p_i - l_p_i) * (x_i - l_p_i) + y_l

            diff = np.asarray([l_func(x, l_p, r_p) for x in self.data[0, :]])

            self.data[1, :] -= diff
            self.data[1, :] -= self.data[1, :].min()
            self.data[0, :] -= self._x_shift_to_centre()
            if is_plot:
                self.refresh_canvas.emit(True)
        elif mode == 'manual':
            self.cid_press = self.canvas.mpl_connect(
                'button_press_event', self._on_press
            )

    def get_max(self, mode='direct'):
        if mode == 'direct':
            return np.max(self.data[1, :])
        elif mode == 'fit':
            self._target(is_plot=False)
            _, _, extra_res = self._fit(fit_fun='pseudo_voigt', is_plot=0)
            try:
                step_time = self.attr['_STEPTIME']
            except KeyError:
                step_time = 1
            intensity = extra_res[0] * extra_res[1] / step_time
            return intensity
