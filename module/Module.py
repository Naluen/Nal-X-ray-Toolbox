import abc
import logging
from functools import partial

import numpy
import numpy as np
from PyQt5 import QtCore, QtWidgets
from matplotlib import pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit
from scipy.special._ufuncs import wofz


class Module(QtCore.QObject):
    send_param = QtCore.pyqtSignal(dict)
    update_gui_cfg = QtCore.pyqtSignal(dict)

    def __init__(self):
        super(Module, self).__init__()
        self.param = {}

    @property
    @abc.abstractmethod
    def name(self):
        pass

    def _build_widget(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        for i in self.param:
            logging.debug("{0}: {1}".format(i, type(self.param[i])))
            if isinstance(self.param[i], (bool, numpy.bool_)):
                logging.info("Building boolean widget...")
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QHBoxLayout()
                qradiobox = QtWidgets.QRadioButton(i)
                qradiobox.setChecked(self.param[i])
                qradiobox.toggled.connect(partial(self._upt_param, i))
                sub_layout.addWidget(qradiobox)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], str):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QVBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                qline = QtWidgets.QLineEdit(self.param[i])
                qline.textChanged.connect(partial(self._upt_param, i))
                sub_layout.addWidget(qline)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], (int, numpy.int_)):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QHBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                p_spin = QtWidgets.QSpinBox()
                p_spin.setMinimum(0)
                p_spin.setMaximum(10000000)
                p_spin.setSingleStep(1)
                p_spin.setValue(self.param[i])
                p_spin.valueChanged.connect(partial(self._upt_param, i))
                sub_layout.addWidget(p_spin)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], (float, numpy.float_)):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QHBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                qline = QtWidgets.QLineEdit(self.param[i])
                qline.textChanged.connect(partial(self._upt_param, i))
                sub_layout.addWidget(qline)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            else:
                pass

        widget.setLayout(layout)

        return widget

    def _upt_param(self, key='', value=''):
        print(key, value)
        self.param[key] = value


class FileModule(Module):
    def __init__(self):
        super(FileModule, self).__init__()
        self.file = None

    @property
    @abc.abstractmethod
    def name(self):
        pass

    @property
    @abc.abstractmethod
    def supp_type(self):
        # Supportive file type.
        # Accept str and any other type could be changed into list.
        pass

    @abc.abstractmethod
    def file2narray(self):
        na = numpy.array([])
        return na

    def get_file(self, file):
        self.file = file


class ProcModule(Module):
    def __init__(self):
        super(ProcModule, self).__init__()
        self.figure = plt.figure("self")
        self.param = {}

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    @abc.abstractmethod
    def supp_type(self):
        # Supportive file type.
        # Accept str and any other type could be changed into list.
        pass

    @staticmethod
    def _bragg_angle_cal(lattice, xtal_hkl):
        """
        Calculation the bragg angle based on the crystal miller
        index.
        >>> hkl_l = [(0, 0, 2), (0, 0, 4), (0, 0, 6), (2, 2, -4)]
        >>> hkl_d = {i: RCurveProc().bragg_angle_cal(0.54505, i) for i in hkl_l}
        >>> assert abs(hkl_d[(0, 0, 2)]-32.8) < 0.1
        """
        LAMBDA = 0.154055911278

        rms = lambda x: np.sqrt(np.sum(np.asarray(x) ** 2))
        bragg_angle = np.arcsin(
            LAMBDA / (2 * lattice / rms(xtal_hkl))
        )

        return np.rad2deg(bragg_angle) * 2

    @abc.abstractmethod
    def plot(self):
        self.figure.clf()
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

    def _save(self):
        plt.figure(self.figure.number)
        tp_d = self.figure.canvas.get_supported_filetypes()
        filter_s = ";;".join(["{0} (*.{1})".format(tp_d[i], i) for i in tp_d])

        file_n = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QFileDialog(),
            caption="Save File...",
            directory='/',
            filter=filter_s,
        )
        if file_n:
            plt.savefig(
                file_n[0],
                transparent=True,
                dpi=300,
                bbox_inches='tight',
            )

    def set_data(self, data, attr, *arg, **kwargs):
        self.data = data[()]
        self.attr = dict(attr)
        for i in self.param:
            if i in self.attr:
                self.param[i] = self.attr[i]

    def closeEvent(self, event):
        self.attr.update(self.param)
        self.send_param.emit(dict(self.attr))
        event.accept()


class OneDProcModule(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(OneDProcModule, self).__init__()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    @abc.abstractmethod
    def supp_type(self):
        # Supportive file type.
        # Accept str and any other type could be changed into list.
        pass

    @property
    def fun_dict(self):
        return {
            'pseudo_voigt': self.pseudo_voigt_func,
            'voigt': self.voigt_func,
            'lorentz': self.lorentzian_func,
            'gaussian': self.gaussian_func,
        }

    @staticmethod
    def gaussian_func(x, alpha):
        """ Return Gaussian line shape at x with HWHM alpha """
        return np.sqrt(np.log(2) / np.pi) / alpha * np.exp(
            -(x / alpha) ** 2 * np.log(2))

    @staticmethod
    def lorentzian_func(x, gamma):
        """ Return Lorentzian line shape at x with HWHM gamma """
        return gamma / np.pi / (x ** 2 + gamma ** 2)

    @staticmethod
    def voigt_func(x, alpha, gamma):
        """
        Return the Voigt line shape at x with Lorentzian component HWHM
        gamma and Gaussian component HWHM alpha.
        """
        sigma = alpha / np.sqrt(2 * np.log(2))
        wofz_v = np.real(
            wofz(((x - 14.22) + 1j * gamma) / sigma / np.sqrt(2)))

        return wofz_v / sigma / np.sqrt(2 * np.pi)

    @staticmethod
    def pseudo_voigt_func(x, alpha, gamma, mu):
        def gaussian_func(x, alpha):
            """ Return Gaussian line shape at x with HWHM alpha """
            return np.sqrt(np.log(2) / np.pi) / alpha * np.exp(
                -(x / alpha) ** 2 * np.log(2))

        def lorentzian_func(x, gamma):
            """ Return Lorentzian line shape at x with HWHM gamma """
            return gamma / np.pi / (x ** 2 + gamma ** 2)

        return mu * gaussian_func(x, alpha) + (
                1 - mu) * lorentzian_func(x, gamma)

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
        self.refresh_canvas.emit(True)

    def _fit(self, fit_fun, is_plot=True):
        """
        Fit the y data with selected function and plot.
        :return:
        """
        x = self.data[0, :]
        y = self.data[1, :]

        popt, pcov = curve_fit(fit_fun, x, y)
        plt.figure(self.figure.number)

        fun_max = fit_fun(0, *popt)
        p = np.abs(fit_fun(x, *popt) - fun_max / 2).argsort()[:2]
        fwhm = np.abs(self.data[0, :][p[0]] - self.data[0, :][p[1]])
        self._res = (fun_max, fwhm)

        if is_plot:
            self.figure.gca().plot(
                x,
                fit_fun(x, *popt),
                'r-',
            )
            self.canvas.draw()

    def _filter(self):
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
            self.data[0, :] -= self.data[0, :][np.argmax(self.data[1, :])]
            if is_plot:
                self.refresh_canvas.emit(True)
        elif mode == 'manual':
            self.cid_press = self.canvas.mpl_connect(
                'button_press_event', self._on_press
            )
