from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)

from module.Module import OneDProcModule
from module.RawFile import RawFile
from module.SinScaProc import SinScaProc


class RCurveProc(OneDProcModule):

    def __init__(self):
        super(RCurveProc, self).__init__()
        self.param = {
            'Thickness of sample': 900,
            'CHI': 11.24,
            'H': 1,
            'K': 1,
            'L': 1,
            'Beam Int': 100000000

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

    @staticmethod
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
            QtGui.QIcon(QtGui.QPixmap('icons/target.png')),
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
            lambda: self._fit(fit_fun=self.fun_dict['pseudo_voigt'])
        )
        fit_tool_button.setDefaultAction(
            pseudo_voigt_fit_action
        )

        fit_tool_button_menu = QtWidgets.QMenu()
        for i in self.fun_dict:
            fit_tool_button_menu.addAction(
                i,
                lambda: self._fit(fit_fun=self.fun_dict[i])
            )
        fit_tool_button.setMenu(fit_tool_button_menu)

        self._toolbar.addWidget(fit_tool_button)

        # Result action
        self.res_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/experiment-results.png')),
            "Results..."
        )
        self.res_action.triggered.connect(self._result)
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
            data, attr = ins.file2narray()
            ins = SinScaProc()
            ins.set_data(data, attr)
            inte = ins.get_max() * 8940
            plt.figure(self.figure.number)
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
    set_h_box_v = QtCore.pyqtSignal(str)
    set_k_box_v = QtCore.pyqtSignal(str)
    set_l_box_v = QtCore.pyqtSignal(str)

    def _build_hkl_box(self):
        self.hkl_wd = QtWidgets.QWidget()
        sub_hkl_layout = QtWidgets.QVBoxLayout()

        horizontal_layout = QtWidgets.QHBoxLayout()
        h_box = QtWidgets.QLineEdit(str(self.param['H']))
        h_box.setInputMask("#9")
        h_box.textChanged.connect(partial(self.param.__setitem__, 'H'))
        self.set_h_box_v.connect(h_box.setText)
        k_box = QtWidgets.QLineEdit(str(self.param['K']))
        k_box.setInputMask("#9")
        k_box.textChanged.connect(partial(self.param.__setitem__, 'K'))
        self.set_k_box_v.connect(k_box.setText)
        l_box = QtWidgets.QLineEdit(str(self.param['L']))
        l_box.setInputMask("#9")
        l_box.textChanged.connect(partial(self.param.__setitem__, 'L'))
        self.set_l_box_v.connect(l_box.setText)

        horizontal_layout.addWidget(QtWidgets.QLabel("H:"))
        horizontal_layout.addWidget(h_box)
        horizontal_layout.addWidget(QtWidgets.QLabel("K:"))
        horizontal_layout.addWidget(k_box)
        horizontal_layout.addWidget(QtWidgets.QLabel("L:"))
        horizontal_layout.addWidget(l_box)

        sub_hkl_layout.addWidget(QtWidgets.QLabel("Choose the HKL:"))
        sub_hkl_layout.addLayout(horizontal_layout)
        self.hkl_wd.setLayout(sub_hkl_layout)

    # =========================================================================

    def _fraction_calculation_param_dialog(self):
        q_dialog = QtWidgets.QDialog()

        q_t_wd = QtWidgets.QWidget()
        sub_layout = QtWidgets.QVBoxLayout()
        q_line = QtWidgets.QLineEdit(str(self.param['Thickness of sample']))
        q_line.textChanged.connect(
            partial(self._upt_param, 'Thickness of sample'))
        sub_layout.addWidget(QtWidgets.QLabel("The thickness of sample:"))
        sub_layout.addWidget(q_line)
        q_t_wd.setLayout(sub_layout)

        chi_wd = QtWidgets.QWidget()
        sub_layout = QtWidgets.QVBoxLayout()
        chi_line_edit = QtWidgets.QLineEdit(str(self.param['CHI']))
        chi_line_edit.textChanged.connect(partial(self._upt_param, 'CHI'))
        sub_layout.addWidget(QtWidgets.QLabel("CHI:"))
        sub_layout.addWidget(chi_line_edit)
        chi_wd.setLayout(sub_layout)

        q_push_button = QtWidgets.QPushButton("OK")
        q_push_button.clicked.connect(q_dialog.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(q_t_wd)
        layout.addWidget(chi_wd)
        layout.addWidget(self.q_line_wd)
        layout.addWidget(q_push_button)

        q_dialog.setLayout(layout)

        return q_dialog

    def _result(self):
        if not hasattr(self, '_res'):
            return
        self._tmp_dialog = self._fraction_calculation_param_dialog()
        self._tmp_dialog.exec()

        step_time = self.attr['_STEPTIME']
        step_size = self.attr['_STEP_SIZE']
        intensity = self._res[0] * self._res[1] * step_time / step_size
        two_theta = self._bragg_angle_cal(
            0.54505,
            (
                float(self.param['H']),
                float(self.param['K']),
                float(self.param['L'])
            )
        )
        theta = two_theta / 2
        th = int(self.param['Thickness of sample'])
        bm_int = int(self.param['Beam Int'])
        v = np.deg2rad(step_size) / step_time
        omega = np.deg2rad(22)
        theta = np.deg2rad(theta)
        i_theo_l = self.i_theory(bm_int, v, theta, omega, th, 1)
        res_l = [intensity, i_theo_l, intensity / i_theo_l * 100, "",
                 self._res[1],
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
        self.param.pop('H', None)
        self.param.pop('K', None)
        self.param.pop('L', None)
        self.param.pop('Beam Int', None)
        self._configuration_wd = self._build_widget()
        self.param = _tmp

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
        if 'H' in self.attr:
            self.set_h_box_v.emit(str(self.attr['H']))
        if 'K' in self.attr:
            self.set_k_box_v.emit(str(self.attr['K']))
        if 'L' in self.attr:
            self.set_l_box_v.emit(str(self.attr['L']))
