import logging
import os
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm

from module.Module import BasicToolBar, ProcModule
from module.OneDScanProc import OneDScanProc

LAMBDA = 0.154055911278
LATTICE_GAP = 0.54505


def _bragg_angle_cal(lattice, xtal_hkl):
    """
    Calculation the bragg angle based on the crystal miller
    index.
    >>> hkl_l = [(0, 0, 2), (0, 0, 4), (0, 0, 6), (2, 2, -4)]
    >>> hkl_d = {i: _bragg_angle_cal(0.54505, i) for i in hkl_l}
    >>> assert abs(hkl_d[(0, 0, 2)]-32.8) < 0.1
    """

    rms = lambda x: np.sqrt(np.sum(np.asarray(x) ** 2))
    bragg_angle = np.arcsin(LAMBDA / (2 * lattice / rms(xtal_hkl)))

    return np.rad2deg(bragg_angle) * 2


class RSMProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self, *args):

        super(RSMProc, self).__init__(*args)

        self.param = {
            "OMEGA_SHIFT": "0",
            "ENABLE_ABSOLUTE_MODE": True
        }
        self.figure = plt.figure(figsize=(10, 10))
        self._build_plot_widget()

        self._lines = []
        self._click_count = 0
        self._click_point_list = []

        self.xi = None  # X axis data
        self.yi = None  # Y axis data
        self.zi = None  # Z axis data

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RMS",

    def _build_plot_widget(self):
        super(RSMProc, self)._build_plot_widget()

        self._qpushbutton_enable_select_area = QtWidgets.QPushButton(
            QtGui.QIcon(QtGui.QPixmap("icons/select_area.png")),
            "Select Area...")
        self._qpushbutton_enable_select_area.setCheckable(True)
        self._qpushbutton_enable_select_area.toggled.connect(
            self._enable_cross_select)
        self._toolbar.addWidget(self._qpushbutton_enable_select_area)

        self._qpushbutton_enable_select_line = QtWidgets.QPushButton(
            QtGui.QIcon(QtGui.QPixmap("icons/select_area.png")),
            "Select Line...")
        self._qpushbutton_enable_select_line.setCheckable(True)
        self._qpushbutton_enable_select_line.toggled.connect(
            self._enable_arbitrary_select)
        self._toolbar.addWidget(self._qpushbutton_enable_select_line)

        self._qpushbutton_enable_select_area.toggled.connect(
            lambda: self._qpushbutton_enable_select_line.setEnabled(
                not self._qpushbutton_enable_select_area.isChecked()
            )
        )

        self._qpushbutton_enable_select_line.toggled.connect(
            lambda: self._qpushbutton_enable_select_area.setEnabled(
                not self._qpushbutton_enable_select_line.isChecked()
            )
        )
        # Main Plot Widget
        self._sub_left_layout = QtWidgets.QVBoxLayout()
        self._sub_left_layout.addWidget(self._toolbar)
        self._sub_left_layout.addWidget(self.canvas)
        self._sub_left_layout.addWidget(self._status_bar)
        # Slice Plot Widget
        self._x_slice = OneDScanProc()
        self._y_slice = OneDScanProc()
        self._x_slider = SliderLineEditLayout(self)
        self._x_slider.slider_bar.valueChanged.connect(
            lambda: self._slice_cross_area(
                width_y=self._y_slider.width,
                width_x=self._x_slider.width)
        )
        self._y_slider = SliderLineEditLayout(self)
        self._y_slider.slider_bar.valueChanged.connect(
            lambda: self._slice_cross_area(
                width_x=self._x_slider.width,
                width_y=self._y_slider.width)
        )
        self._sub_right_layout = QtWidgets.QVBoxLayout()
        self._sub_right_layout.addWidget(self._x_slice.plot_widget)
        self._sub_right_layout.addLayout(self._x_slider)
        self._sub_right_layout.addWidget(self._y_slice.plot_widget)
        self._sub_right_layout.addLayout(self._y_slider)

        self._main_layout = QtWidgets.QHBoxLayout()
        self._main_layout.addLayout(self._sub_left_layout)
        self._main_layout.addLayout(self._sub_right_layout)

        self.plot_widget.setLayout(self._main_layout)
        self.plot_widget.closeEvent = self.closeEvent
        self.plot_widget.resize(1000, 600)

    def _build_config_widget(self):
        config_widget = QtWidgets.QWidget(self.plot_widget)
        config_layout = QtWidgets.QVBoxLayout()
        config_widget.setLayout(config_layout)

        omega_shift_input_layout = QtWidgets.QVBoxLayout()
        omega_shift_input_layout.addWidget(QtWidgets.QLabel('Omega shift:'))
        omega_shift_line_edit = QtWidgets.QLineEdit()
        omega_shift_line_edit.setText(self.param['OMEGA_SHIFT'])
        omega_shift_line_edit.textChanged.connect(
            partial(self._upt_param, "OMEGA_SHIFT"))
        omega_shift_input_layout.addWidget(omega_shift_line_edit)
        config_layout.addLayout(omega_shift_input_layout)

        enable_absolute_mode_button = QtWidgets.QRadioButton(
            "Enable absolute mode")
        enable_absolute_mode_button.setStatusTip("Swap all the NaN to 0")
        enable_absolute_mode_button.setChecked(
            self.param["ENABLE_ABSOLUTE_MODE"])
        enable_absolute_mode_button.toggled.connect(
            partial(self._upt_param, "ENABLE_ABSOLUTE_MODE"))
        config_layout.addWidget(enable_absolute_mode_button)

        return config_widget

    def _configuration(self):
        widget = self._build_config_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(widget, "RSM")
        self.q_tab_widget.closeEvent = self._configuration_close
        self.q_tab_widget.show()

    @QtCore.pyqtSlot(bool)
    def repaint(self, message):
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Scan Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in self.attr.items()
        ]))
        # ====================================================================

        from scipy.interpolate import griddata
        int_data = self.data.copy()
        w, h = int_data.shape

        try:
            tth = self.attr['two_theta_data'][0].copy()
        except KeyError:
            tth = self.attr.get('TWOTHETA').copy()

        try:
            omega = self.attr.get('OMEGA').copy()
        except KeyError:
            omega = self.attr['omega_data'].copy()
        try:
            phi = self.attr['phi_data'][0]
        except KeyError:
            phi = self.attr['PHI']

        if self.param['OMEGA_SHIFT']:
            try:
                omega -= float(self.param['OMEGA_SHIFT'])
            except ValueError:
                pass

        hkl_l = [(0, 0, 2), (0, 0, 4), (0, 0, 6), (2, 2, -4)]
        hkl_d = {i: _bragg_angle_cal(LATTICE_GAP, i) for i in hkl_l}
        hkl = [i for i in hkl_d if abs(tth[0] - hkl_d[i]) <= 3]
        if len(hkl) is not 1:
            logging.error('HKL Value Error')
            hkl = [0, 0, 0]
        else:
            hkl = hkl[0]
        self.attr['HKL'] = np.asarray(hkl)
        tth, omega = np.meshgrid(tth, omega)
        s_mod = 4.*np.pi / LAMBDA * np.sin(np.radians(tth / 2.)) / 10
        psi = omega - tth / 2.
        s_x = s_mod * np.sin(np.radians(psi))
        s_z = s_mod * np.cos(np.radians(psi))

        s_x = -s_x if abs(phi) < 2 else s_x

        xi = np.linspace(s_x.min(), s_x.max(), w)
        yi = np.linspace(s_z.min(), s_z.max(), h)
        xx, yy = np.meshgrid(xi, yi)
        zi = griddata(
            (s_x.flatten(), s_z.flatten()),
            int_data.flatten(), (xx, yy),
            method='linear')

        self.figure.clf()
        plt.figure(self.figure.number)
        im = plt.imshow(
            zi,
            origin='lower',
            norm=LogNorm(10, 100),
            extent=[s_x.min(), s_x.max(),
                    s_z.min(), s_z.max()])

        plt.xlabel("$Q_x$ ($Å^{-1}$)", fontsize=16)
        plt.ylabel("$Q_z$ ($Å^{-1}$)", fontsize=16)
        plt.xticks(fontsize=16)
        plt.yticks(fontsize=16)

        # plt.gca().set_xlim(left=0.46, right=0.53)
        # plt.gca().set_ylim(bottom=4.55, top=4.61)

        cb = self.figure.colorbar(
            im,
            format="%.2e",
            extend='max',
            # norm=LogNorm(10, 1000),
            pad=.015,
            fraction=.039
        )
        cb.ax.tick_params(labelsize=16)
        cb.set_label(r'Intensity $(Counts\ per\ second)$', fontsize=16)

        self.xi = xi
        self.yi = yi
        self.zi = zi

        self.canvas.draw()

        self.canvas.mpl_connect('scroll_event', self._zoom_fun)

    def plot(self):
        """Plot Image."""
        self.repaint("")

        self.plot_widget.show()
        self.canvas.mpl_connect(
            'motion_notify_event', self.on_motion_show_data)

        return self.plot_widget

    @staticmethod
    def _fill_array(array):
        return np.asanyarray([i for i in array if i is not []])

    @staticmethod
    def _int2coor(axis, ind):
        coor = (np.abs(axis - ind)).argmin()

        return coor

    def _clean_lines(self):
        if self._lines:
            plt.figure(self.figure.number)
            for i in self._lines:
                try:
                    i.remove()
                except ValueError or TypeError:
                    continue
            self._lines = []
        else:
            return

    def _enable_cross_select(self, signal):
        if signal:
            self.cid_click = self.canvas.mpl_connect(
                'button_press_event', self._mpl_double_click_select)
            self.cid_motion = self.canvas.mpl_connect(
                'motion_notify_event', self._mpl_on_motion)
        else:
            self.canvas.mpl_disconnect(self.cid_click)
            self.canvas.mpl_disconnect(self.cid_motion)

    def _mpl_double_click_select(self, event):
        """Plot the line and draw the profile when clicked.

        Double click for cross_line, single click for ab_line."""
        if hasattr(event, "button"):
            if event.inaxes != self.figure.axes[0]:
                return

            if event.button == 1 and event.dblclick:
                self._cur_centre = (event.xdata, event.ydata)
                self._slice_cross_area(self._cur_centre)

    def _slice_cross_area(self, *args, width_x=0.05, width_y=0.05):
        try:
            xi = self.xi
            yi = self.yi
            s_data = self.zi
        except AttributeError:
            return

        self._clean_lines()

        if args:
            (x_dt, y_dt) = args[0]
        else:
            try:
                (x_dt, y_dt) = self._cur_centre
            except AttributeError:
                return
        x_min_dt = x_dt - width_x / 2
        y_min_dt = y_dt - width_y / 2
        x_max_dt = x_dt + width_x / 2
        y_max_dt = y_dt + width_y / 2

        [x, x_min,
         x_max] = [self._int2coor(xi, i) for i in [x_dt, x_min_dt, x_max_dt]]
        [y, y_min,
         y_max] = [self._int2coor(yi, i) for i in [y_dt, y_min_dt, y_max_dt]]

        h_lines, = plt.plot(
            [x_min_dt, x_max_dt, x_max_dt, x_min_dt, x_min_dt],
            [yi.min(), yi.min(), yi.max(), yi.max(), yi.min()],
            color='C1'
        )

        v_lines, = plt.plot(
            [xi.min(), xi.min(), xi.max(), xi.max(), xi.min()],
            [y_max_dt, y_min_dt, y_min_dt, y_max_dt, y_max_dt],
            color='C2'
        )

        width, length = s_data.shape
        y_min = max(y_min, 0)
        x_min = max(x_min, 0)
        y_max = min(y_max, width)
        x_max = min(x_max, length)
        if self.param['ENABLE_ABSOLUTE_MODE']:
            s_data[np.isnan(s_data)] = 0

        data_x = s_data[y, :] if width_x < 1e-10 else np.sum(
            s_data[y_min:y_max, :], axis=0)
        data_y = s_data[:, x] if width_y < 1e-10 else np.sum(
            s_data[:, x_min:x_max], axis=1)

        self.canvas.draw()
        data = [np.vstack((yi, data_y)), np.vstack((xi, data_x))]
        lines = [h_lines, v_lines]

        self.canvas.draw()
        self._lines.extend(lines)

        self._x_slice.set_data(data[0], {'STEPPING_DRIVE1': 'Qx'})
        self._x_slice.figure.clf()
        self._x_slice.repaint("")

        self._y_slice.set_data(data[1], {'STEPPING_DRIVE1': 'Qz'})
        self._y_slice.figure.clf()
        self._y_slice.repaint("")

        return lines, data,

    def _enable_arbitrary_select(self, signal):
        if signal:
            self.cid_click = self.canvas.mpl_connect(
                'button_press_event', self._mpl_single_click_select
            )
        else:
            self.canvas.mpl_disconnect(self.cid_click)

    def _mpl_single_click_select(self, event):
        if hasattr(event, "button"):
            if event.inaxes != self.figure.axes[0]:
                return

            if event.button == 1:
                self._click_count += 1
                self._click_point_list.append(event)

                if not self._click_count % 2:
                    self._slice_arbitrary_line(self._click_point_list)
                    self._click_point_list = []

    def _slice_arbitrary_line(self, points_list):
        try:
            xi = self.xi
            yi = self.yi
            s_data = self.zi
        except AttributeError:
            return

        self._clean_lines()

        num = 1000
        x0_data = points_list[0].xdata
        x1_data = points_list[1].xdata
        x_axis = np.linspace(x0_data, x1_data, num)
        y0_data = points_list[0].ydata
        y1_data = points_list[1].ydata
        y_axis = np.linspace(y0_data, y1_data, num)

        x0 = self._int2coor(xi, x0_data)
        x1 = self._int2coor(xi, x1_data)
        y0 = self._int2coor(yi, y0_data)
        y1 = self._int2coor(yi, y1_data)

        x, y = np.linspace(x0, x1, num), np.linspace(y0, y1, num)

        # Extract the values along the line, using cubic interpolation
        from scipy import ndimage
        zi = ndimage.map_coordinates(s_data, np.vstack((y, x)), order=1)
        # zi = s_data[y.astype(np.int), x.astype(np.int)]

        data = [np.vstack((x_axis, zi)), np.vstack((y_axis, zi))]

        plt.figure(self.figure.number)
        line, = plt.plot([x0_data, x1_data], [y0_data, y1_data], 'ro-')
        self.canvas.draw()
        self._lines.extend([line])

        self._x_slice.set_data(data[0], {'STEPPING_DRIVE1': 'Sx'})
        self._x_slice.figure.clf()
        self._x_slice.repaint("")

        self._y_slice.set_data(data[1], {'STEPPING_DRIVE1': 'Sz'})
        self._y_slice.figure.clf()
        self._y_slice.repaint("")

    def _mpl_on_motion(self, event):
        """Change the line and status bar during the mouse moving."""
        pass
        # if event.inaxes != self.figure.axes[0]:
        #     return

        # x, y = event.xdata, event.ydata
        # self.ui.statusbar.showMessage(
        #     'x={0:.3f}, y={1:.3f}'.format(x, y))
        # if hasattr(self, '_count'):
        #     if self._count % 2 == 1:
        #         x0, y0 = self._cur_centre[0]

        #         self.clean_lines()
        #         ab_line, = self.figure.axes[0].plot(
        #             [x0, x], [y0, y],
        #             color='#F44336', ls='--', lw=1, alpha=0.61)

        #         self._lines.append(ab_line)

        #         self.canvas.draw()
        #     else:
        #         return

    def _zoom_fun(self, event):
        """ Zoom function based on tacaswell's answer at
        https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
        :param event:
        :return:
        """
        base_scale = 1.1
        # get the current x and y limits
        ax = self.figure.axes[0]
        cur_x_lim = ax.get_xlim()
        cur_y_lim = ax.get_ylim()
        cur_x_range = (cur_x_lim[1] - cur_x_lim[0]) * .5
        cur_y_range = (cur_y_lim[1] - cur_y_lim[0]) * .5
        x_data = event.xdata  # get event x location
        y_data = event.ydata  # get event y location
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
        # set new limits
        ax.set_xlim([x_data - cur_x_range * scale_factor,
                     x_data + cur_x_range * scale_factor])
        ax.set_ylim([y_data - cur_y_range * scale_factor,
                     y_data + cur_y_range * scale_factor])
        self.canvas.draw()

    def on_motion_show_data(self, event):
        if event.inaxes != plt.gca():
            return

        self._status_bar.showMessage(
            "({0:.2f}, {1:.2f} )".format(event.xdata, event.ydata))


class SliderLineEditLayout(QtWidgets.QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__()
        self.label = QtWidgets.QLabel("Width:")
        self.addWidget(self.label)

        self.slider_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_bar.setMaximum(100)
        self.slider_bar.setMinimum(1)
        self.slider_bar.setValue(5)
        self.slider_bar.setSingleStep(1)
        self.addWidget(self.slider_bar)

        self.line_edit = QtWidgets.QLineEdit()
        self.addWidget(self.line_edit)

        try:
            self.slider_bar.valueChanged.connect(
                lambda: self.line_edit.setText(
                    str(self.slider_bar.value() / 100))
            )
            self.line_edit.textChanged.connect(
                lambda: self.slider_bar.setValue(
                    float(self.line_edit.text()) * 100)
            )
        except ValueError:
            pass

        self.width = 0.05

        self.slider_bar.valueChanged.connect(
            lambda: setattr(self, "width",
                            float(self.slider_bar.value() / 100))
        )
