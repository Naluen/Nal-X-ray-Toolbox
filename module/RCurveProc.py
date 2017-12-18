import logging
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from scipy import signal
from scipy.optimize import curve_fit
from scipy.special import wofz

from module.Module import OneDProcModule
from module.RawFile import RawFile

HKL_DICT = OrderedDict({
    '002': [0, 0, 2],
    '004': [0, 0, 4],
    '006': [0, 0, 6],
    '-2-24': [-2, -2, 4],
})
LAMBDA = 0.154055911278


def _bragg_angle_cal(lattice, xtal_hkl):
    """
    Calculation the bragg angle based on the crystal miller
    index.
    >>> hkl_l = [(0, 0, 2), (0, 0, 4), (0, 0, 6), (2, 2, -4)]
    >>> hkl_d = {i: _bragg_angle_cal(0.54505, i) for i in hkl_l}
    >>> assert abs(hkl_d[(0, 0, 2)]-32.8) < 0.1
    """

    rms = lambda x: np.sqrt(np.sum(np.asarray(x) ** 2))
    bragg_angle = np.arcsin(
        LAMBDA / (2 * lattice / rms(xtal_hkl))
    )

    return np.rad2deg(bragg_angle) * 2


def i_theory(i_0, v, theta, omega, th, index):
    RO2 = 7.94E-30
    LAMBDA = 1.5418E-10
    F_GAP = 3249.001406
    L = 1.846012265
    P = 0.853276107
    V_A = 5.4506E-10 ** 3
    U = 1000000 / 37.6416
    c_0 = (
            np.sin(2 * theta - omega) /
            (np.sin(2 * theta - omega) + np.sin(omega))
    )
    c_1 = (
            1 - np.exp(
        0 - U * th / 1E10 * (
                1 / np.sin(omega) + 1 / np.sin(2 * theta - omega)
        )
    )
    )
    c_2 = RO2 * LAMBDA ** 3 * F_GAP * P * L / V_A ** 2

    i_theo = i_0 * c_0 * c_1 * c_2 * index / (v * U)

    return i_theo


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


FUN_DICT = {
    'pseudo_voigt': pseudo_voigt_func,
    'voigt': voigt_func,
    'lorentz': lorentzian_func,
    'gaussian': gaussian_func,
}


class RCurveProc(OneDProcModule):

    def __init__(self):
        super(RCurveProc, self).__init__()
        self.param = {
            'Thickness of sample': 1,
            'HKL': 0,
            'Beam Int': 1

        }
        self._peak_side_point = []
        self._build_plot_widget()
        self._build_intensity_input_line_edit()
        self._build_hkl_box()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RockingCurve",

    # =======Main Canvas=======================================================
    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._toolbar = QtWidgets.QToolBar()
        self._toolbar.setMinimumHeight(60)
        self._toolbar.setIconSize(QtCore.QSize(30, 30))

        # General part of toolbar==============================================
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

        # Specific part of class.==============================================
        # Filter tool button.
        filter_tool_button = QtWidgets.QToolButton()

        butter_filter_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/filter.png')),
            "Filter",
        )
        butter_filter_action.triggered.connect(self._filter)
        filter_tool_button.setDefaultAction(butter_filter_action)

        filter_tool_button_menu = QtWidgets.QMenu()
        filter_tool_button_menu.addAction(
            "Butter Filter(Default)", self._filter
        )
        filter_tool_button_menu.addAction(
            "Binning", self._binning_data
        )

        filter_tool_button.setMenu(filter_tool_button_menu)

        self._toolbar.addWidget(filter_tool_button)

        # Target tool bar
        target_tool_button = QtWidgets.QToolButton()

        auto_target_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/cross-shaped-target.png')),
            "Auto align data",
        )
        auto_target_action.triggered.connect(lambda: self._target(mode='auto'))
        target_tool_button.setDefaultAction(auto_target_action)

        target_tool_button_menu = QtWidgets.QMenu()
        target_tool_button_menu.addAction(
            "Auto(Default)", lambda: self._target(mode='auto')
        )
        target_tool_button_menu.addAction(
            "Manual", lambda: self._target(mode='manual')
        )

        target_tool_button.setMenu(target_tool_button_menu)

        self._toolbar.addWidget(target_tool_button)

        # Fit tool button
        fit_tool_button = QtWidgets.QToolButton()

        pseudo_voigt_fit_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/curve.png')),
            "Voigt Profile...",
        )
        pseudo_voigt_fit_action.triggered.connect(
            lambda: self._fit(fit_fun=FUN_DICT['pseudo_voigt'])
        )
        fit_tool_button.setDefaultAction(
            pseudo_voigt_fit_action
        )

        fit_tool_button_menu = QtWidgets.QMenu()
        for i in FUN_DICT:
            fit_tool_button_menu.addAction(
                i,
                lambda: self._fit(fit_fun=FUN_DICT[i])
            )
        fit_tool_button.setMenu(fit_tool_button_menu)

        self._toolbar.addWidget(fit_tool_button)

        # Result action
        self.res_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/experiment-results.png')),
            "Results..."
        )
        self.res_action.triggered.connect(self._result)
        self.res_action.setEnabled(False)
        self._toolbar.addAction(self.res_action)

        self.plot_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self._toolbar)
        self.layout.addWidget(self.canvas)
        # self.layout.addWidget(QtWidgets.QStatusBar())
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
        plt.ylabel("{0}".format("Intensity(CPS)"))
        self.canvas.draw()

    # ========Intensity input line edit.=======================================
    set_q_int_line_v = QtCore.pyqtSignal(int)

    def _build_intensity_input_line_edit(self):
        self.q_line_wd = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Beam Intensity"))
        self.q_int_line = QtWidgets.QLineEdit(str(self.param['Beam Int']))
        self.q_int_line.textChanged.connect(
            partial(self.param.__setitem__, 'Beam Int'))
        q_int_button = self.q_int_line.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/more.png')),
            QtWidgets.QLineEdit.TrailingPosition)
        q_int_button.triggered.connect(self._get_bm_int)
        layout.addWidget(self.q_int_line)
        self.q_line_wd.setLayout(layout)
        self.set_q_int_line_v.connect(self._set_q_int_line)

    @QtCore.pyqtSlot(int)
    def _set_q_int_line(self, msg):
        self.q_int_line.setText(str(msg))
        self.param['Beam Int'] = int(msg)

    def _get_bm_int(self):
        def file2int(i):
            ins = RawFile()
            ins.get_file(i)
            data, _ = ins.file2narray()
            inte = np.max(data[1, :]) * 8940
            del ins
            return inte

        file_names = QtWidgets.QFileDialog.getOpenFileNames(
            caption='Open intensity file...',
            directory="/",
            filter="Raw file (*.raw)"
        )
        source_file_list = file_names[0]
        if not source_file_list:
            return
        int_l = [file2int(str(i)) for i in source_file_list]
        beam_int = np.mean(np.asarray(int_l))
        self.set_q_int_line_v.emit(beam_int)

    # ========Intensity input line edit.=======================================
    set_hkl_box_v = QtCore.pyqtSignal(int)

    def _build_hkl_box(self):
        self.hkl_wd = QtWidgets.QWidget()
        sub_hkl_layout = QtWidgets.QVBoxLayout()
        self.hkl_box = QtWidgets.QComboBox()
        self.hkl_box.addItems(list(HKL_DICT.keys()))
        self.hkl_box.setCurrentIndex(self.param['HKL'])
        self.hkl_box.currentIndexChanged.connect(
            partial(self.param.__setitem__, 'HKL')
        )
        sub_hkl_layout.addWidget(QtWidgets.QLabel("Choose the HKL:"))
        sub_hkl_layout.addWidget(self.hkl_box)
        self.hkl_wd.setLayout(sub_hkl_layout)

        self.set_hkl_box_v.connect(self._set_hkl_box)

    @QtCore.pyqtSlot(int)
    def _set_hkl_box(self, msg):
        self.hkl_box.setCurrentIndex(msg)
        self.param['HKL'] = int(msg)

    # =========================================================================

    def _filter(self):
        arg = signal.butter(5, 0.1)
        self.data[1, :] = signal.filtfilt(
            *arg, self.data[1, :], method="gust")
        self.refresh_canvas.emit(True)

    def _target(self, mode='auto'):

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

    def _fit(self, fit_fun):
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
        self.res_action.setEnabled(True)

        plt.plot(
            x,
            pseudo_voigt_func(x, *popt),
            'r-',
        )
        self.canvas.draw()

    def _fraction_calculation_param_dialog(self):
        q_dialog = QtWidgets.QDialog()

        q_t_wd = QtWidgets.QWidget()
        sub_layout = QtWidgets.QVBoxLayout()
        q_line = QtWidgets.QLineEdit(str(self.param['Thickness of sample']))
        q_line.textChanged.connect(
            partial(self.param.__setitem__, 'Thickness of sample'))
        sub_layout.addWidget(QtWidgets.QLabel("The thickness of sample:"))
        sub_layout.addWidget(q_line)
        q_t_wd.setLayout(sub_layout)

        q_push_button = QtWidgets.QPushButton("OK")
        q_push_button.clicked.connect(q_dialog.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(q_t_wd)
        layout.addWidget(self.q_line_wd)
        layout.addWidget(self.hkl_wd)
        layout.addWidget(q_push_button)

        q_dialog.setLayout(layout)

        return q_dialog

    def _result(self):
        self._tmp_dialog = self._fraction_calculation_param_dialog()
        self._tmp_dialog.exec()

        step_time = self.attr['_STEPTIME']
        step_size = self.attr['_STEP_SIZE']
        intensity = self._res[0] * self._res[1] * step_time / step_size
        theta = _bragg_angle_cal(
            0.54505, list(HKL_DICT.values())[self.param['HKL']]) / 2
        th = int(self.param['Thickness of sample'])
        bm_int = int(self.param['Beam Int'])
        v = np.deg2rad(step_size) / step_time
        omega = np.deg2rad(22)
        theta = np.deg2rad(theta)
        i_theo_l = i_theory(bm_int, v, theta, omega, th, 1)
        res_l = [intensity, i_theo_l, intensity/i_theo_l*100, "", self._res[1],
                 self._res[0], "", bm_int, v, np.rad2deg(theta),
                 np.rad2deg(omega), th]

        self.res_table_wd = QtWidgets.QTableWidget()
        self.res_table_wd.resize(QtCore.QSize(*self.cfg['res_table_wd_size']))
        self.res_table_wd.setColumnCount(1)
        self.res_table_wd.setRowCount(11)

        self.res_table_wd.setVerticalHeaderLabels(
            ["Intensity", "Intensity theory", "Volume Fraction(%)", "",
             "FWHM", "Max", "", "Source Intensity", "Angular Vitesse",
             "Theta", "Omega", "Thickness"]
        )

        for i in range(len(res_l)):
            self.res_table_wd.setItem(
                i, 0,
                QtWidgets.QTableWidgetItem(str(res_l[i]))
            )

        self.res_table_wd.closeEvent = self._res_table_wd_close

        self.res_table_wd.show()

    def _res_table_wd_close(self, event):
        table_size = self.res_table_wd.size()
        table_size = [table_size.width(), table_size.height()]
        self.update_gui_cfg.emit(
            {'MODULE': {self.name: {'res_table_wd_size': table_size}}})
        event.accept()

    # Config Menu.=============================================================
    def _configuration(self):
        _tmp = self.param.copy()
        self.param.pop('HKL', None)
        self.param.pop('Beam Int', None)
        self._configuration_wd = self._build_widget()
        self.param['HKL'] = _tmp['HKL']
        self.param['Beam Int'] = _tmp['Beam Int']

        self._configuration_wd.layout().addWidget(self.q_line_wd)
        self._configuration_wd.layout().addWidget(self.hkl_wd)

        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(self._configuration_wd, self.attr['Type'])
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _close_configuration(self, event):
        self.refresh_canvas.emit(True)
        event.accept()

    # External methods.========================================================
    def get_max(self):
        # TODO(azhou@insa-rennes.fr): Use local max instead of max.
        return np.max(self.data[1, :])

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self._repaint(True)

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr, *args, **kwargs):
        self.data = data[()]
        self.attr = dict(attr)
        self.cfg = args[0]
        for i in self.param:
            if i in self.attr:
                self.param[i] = self.attr[i]
        if 'Beam Int' in self.attr:
            self.set_q_int_line_v.emit(self.attr['Beam Int'])
        if 'HKL' in self.attr:
            self.set_hkl_box_v.emit(self.attr['HKL'])
