import logging
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

from module.OneDScanProc import OneDScanProc
from module.RawFile import RawFile


class RCurveProc(OneDScanProc):

    def __init__(self, *args):

        super().__init__(*args)

        self.param.update({
            'THICKNESS': "900",
            'CHI': "11.24",
            'H': "1",
            'K': "1",
            'L': "1",
            'BEAM_INT': "100000000"

        })
        self._peak_side_point = []
        self.cfg = {}

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RockingCurve",

    def _build_plot_widget(self):
        """
        Build the drawing widget.
        :return:
        """
        super(RCurveProc, self)._build_plot_widget()

        filter_tool_button = QtWidgets.QToolButton()

        # Build butter filter action
        butter_filter_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/filter.png')),
            "Filter",
        )
        butter_filter_action.triggered.connect(self._filter)
        filter_tool_button.setDefaultAction(butter_filter_action)

        # Build the filter selection menu
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
        # Result action
        self.res_action = QtWidgets.QAction(
            QtGui.QIcon(QtGui.QPixmap('icons/experiment-results.png')),
            "Results..."
        )
        self.res_action.triggered.connect(self._result)
        self._toolbar.addAction(self.res_action)

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

        intensity_input_layout = IntensityInputWidget(self.param)
        config_layout.addLayout(intensity_input_layout)

        thickness_input_layout = QtWidgets.QVBoxLayout()
        thickness_input_layout.addWidget(
            QtWidgets.QLabel('Thickness of Sample(\u212B):'))
        thickness_line_edit = QtWidgets.QLineEdit()
        thickness_line_edit.setText(self.param['THICKNESS'])
        thickness_line_edit.setInputMask("999999999")
        thickness_line_edit.textChanged.connect(
            partial(self._upt_param, "THICKNESS")
        )
        thickness_input_layout.addWidget(thickness_line_edit)
        config_layout.addLayout(thickness_input_layout)

        chi_input_layout = QtWidgets.QVBoxLayout()
        chi_input_layout.addWidget(
            QtWidgets.QLabel('CHI:'))
        chi_line_edit = QtWidgets.QLineEdit()
        chi_line_edit.setText(self.param['CHI'])
        chi_line_edit.setValidator(QtGui.QIntValidator(0, 360, chi_line_edit))
        chi_line_edit.textChanged.connect(partial(self._upt_param, "CHI"))
        chi_input_layout.addWidget(chi_line_edit)
        config_layout.addLayout(chi_input_layout)

        hkl_input_layout = HKLInputComboBox(self.param)
        config_layout.addLayout(hkl_input_layout)

        return config_widget

    def _configuration(self):
        self._configuration_wd = self._build_config_widget()

        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(self._configuration_wd, "Rocking Curve")
        self.q_tab_widget.closeEvent = self._configuration_close
        self.q_tab_widget.show()

    @QtCore.pyqtSlot(bool)
    def repaint(self, message=True):
        logging.debug("Re-Paint rocking curve %s" % self)
        if message:
            self.figure.clf()
        plt.figure(self.figure.number)
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
        plt.ylabel("{0}".format("Intensity(CPS)"))
        self.canvas.draw()

    def plot(self):
        """Plot Image."""
        self.figure.clf()
        self.repaint(True)

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr, *args, **kwargs):
        super(RCurveProc, self).set_data(data, attr, *args, **kwargs)
        try:
            self.cfg = args[0]
        except IndexError:
            pass

        return self

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

    def _fraction_calculation_param_dialog(self):
        config_widget = QtWidgets.QDialog(self.plot_widget)
        config_layout = QtWidgets.QVBoxLayout()
        config_widget.setLayout(config_layout)

        intensity_input_layout = IntensityInputWidget(self.param)

        thickness_input_layout = QtWidgets.QVBoxLayout()
        thickness_input_layout.addWidget(
            QtWidgets.QLabel('Thickness of Sample(\u212B):'))
        thickness_line_edit = QtWidgets.QLineEdit()
        thickness_line_edit.setText(self.param['THICKNESS'])
        thickness_line_edit.setInputMask("999999999")
        thickness_line_edit.textChanged.connect(
            partial(self._upt_param, "THICKNESS")
        )
        thickness_input_layout.addWidget(thickness_line_edit)

        chi_input_layout = QtWidgets.QVBoxLayout()
        chi_input_layout.addWidget(
            QtWidgets.QLabel('Thickness of Sample(\u212B):'))
        chi_line_edit = QtWidgets.QLineEdit()
        chi_line_edit.setText(self.param['CHI'])
        chi_line_edit.setValidator(QtGui.QIntValidator(0, 360, chi_line_edit))
        chi_line_edit.textChanged.connect(partial(self._upt_param, "CHI"))
        chi_input_layout.addWidget(chi_line_edit)

        hkl_input_layout = HKLInputComboBox(self.param)

        config_layout.addLayout(intensity_input_layout)
        config_layout.addLayout(thickness_input_layout)
        config_layout.addLayout(hkl_input_layout)
        config_layout.addLayout(chi_input_layout)

        return config_widget

    def _result(self):
        if not hasattr(self, '_recent_fit_res'):
            return
        self._tmp_dialog = self._fraction_calculation_param_dialog()
        self._tmp_dialog.exec()

        try:
            step_time = self.attr['_STEPTIME']
            step_size = self.attr['_STEP_SIZE']
        except KeyError:
            step_time = self.attr['STEP_TIME']
            step_size = self.attr['STEP_SIZE']
        intensity = (
                self._recent_fit_res[0] * self._recent_fit_res[1] *
                step_time / step_size)
        two_theta = self._bragg_angle_cal(
            0.54505,
            (
                int(self.param['H']),
                int(self.param['K']),
                int(self.param['L'])
            )
        )
        theta = two_theta / 2
        th = int(self.param['THICKNESS'])
        bm_int = int(self.param['BEAM_INT'])
        v = np.deg2rad(step_size) / step_time
        omega = np.deg2rad(22)
        theta = np.deg2rad(theta)
        i_theo_l = self.i_theory(bm_int, v, theta, omega, th, 1)
        res_l = [intensity, i_theo_l, intensity / i_theo_l * 100, "",
                 self._recent_fit_res[1],
                 self._recent_fit_res[0], "", bm_int, v, np.rad2deg(theta),
                 np.rad2deg(omega), th]

        self.res_table_wd = QtWidgets.QTableWidget()
        try:
            self.res_table_wd.resize(
                QtCore.QSize(*self.cfg['res_table_wd_size']))
        except (AttributeError, KeyError):
            pass
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

        # self.res_table_wd.closeEvent = self._res_table_wd_close

        self.res_table_wd.show()

    # def _res_table_wd_close(self, event):
    #     table_size = self.res_table_wd.size()
    #     table_size = [table_size.width(), table_size.height()]
    #     self.update_gui_cfg.emit(
    #         {'MODULE': {self.name: {'res_table_wd_size': table_size}}})
    #     event.accept()


class IntensityInputWidget(QtWidgets.QVBoxLayout):
    def __init__(self, linked_param):
        super().__init__()

        self._int_line_edit = QtWidgets.QLineEdit(
            str(linked_param['BEAM_INT']))
        self._int_line_edit.textChanged.connect(
            partial(linked_param.__setitem__, 'BEAM_INT'))
        q_int_button = self._int_line_edit.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/more.png')),
            QtWidgets.QLineEdit.TrailingPosition
        )
        q_int_button.triggered.connect(self._get_beam_intensity)

        self.addWidget(QtWidgets.QLabel("Beam Intensity"))
        self.addWidget(self._int_line_edit)

    def _get_beam_intensity(self):
        def file2int(i):
            file_instance = RawFile()
            file_instance.get_file(i)
            data, attr = file_instance.get_data()
            del file_instance

            scan_instance = OneDScanProc()
            scan_instance.set_data(data, attr)
            maxmium_int = scan_instance.get_max(mode='direct')

            return maxmium_int

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
        self._int_line_edit.setText(str(beam_int))


class HKLInputComboBox(QtWidgets.QVBoxLayout):
    def __init__(self, linked_dict):
        super().__init__()
        horizontal_layout = QtWidgets.QHBoxLayout()
        h_box = QtWidgets.QLineEdit(str(linked_dict['H']))
        h_box.setInputMask("#9")
        h_box.textChanged.connect(partial(linked_dict.__setitem__, 'H'))
        k_box = QtWidgets.QLineEdit(str(linked_dict['K']))
        k_box.setInputMask("#9")
        k_box.textChanged.connect(partial(linked_dict.__setitem__, 'K'))
        l_box = QtWidgets.QLineEdit(str(linked_dict['L']))
        l_box.setInputMask("#9")
        l_box.textChanged.connect(partial(linked_dict.__setitem__, 'L'))

        horizontal_layout.addWidget(QtWidgets.QLabel("H:"))
        horizontal_layout.addWidget(h_box)
        horizontal_layout.addWidget(QtWidgets.QLabel("K:"))
        horizontal_layout.addWidget(k_box)
        horizontal_layout.addWidget(QtWidgets.QLabel("L:"))
        horizontal_layout.addWidget(l_box)

        self.addWidget(QtWidgets.QLabel("Choose the HKL:"))
        self.addLayout(horizontal_layout)
