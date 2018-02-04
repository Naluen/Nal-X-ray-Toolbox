import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm

from module.Module import ProcModule, BasicToolBar
from module.OneDScanProc import OneDScanProc

LAMBDA = 0.154055911278
LATTICE_GAP = 0.54505


# TODO Select area.


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

    def __init__(self):
        super(RSMProc, self).__init__()
        self.param = {}
        self.figure = plt.figure()
        self._build_plot_widget()

        self._lines = []

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RMS",

    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Expanding)
        # Main Plot ToolBar
        self._toolbar = BasicToolBar(self)

        self._qpushbutton_enable_select_area = QtWidgets.QPushButton(
            QtGui.QIcon(QtGui.QPixmap("icons/select_area.png")),
            "Select Area..."
        )
        self._qpushbutton_enable_select_area.setCheckable(True)
        self._qpushbutton_enable_select_area.toggled.connect(
            self._enable_cross_select)
        self._toolbar.addWidget(self._qpushbutton_enable_select_area)
        # Main Plot Widget
        self._sub_left_layout = QtWidgets.QVBoxLayout()
        self._sub_left_layout.addWidget(self._toolbar)
        self._sub_left_layout.addWidget(self.canvas)
        # Slice Plot Widget
        self._x_slice = OneDScanProc()
        self._y_slice = OneDScanProc()
        self._sub_right_layout = QtWidgets.QVBoxLayout()
        self._sub_right_layout.addWidget(self._x_slice.plot_widget)
        self._sub_right_layout.addWidget(self._y_slice.plot_widget)

        self._main_layout = QtWidgets.QHBoxLayout()
        self._main_layout.addLayout(self._sub_left_layout)
        self._main_layout.addLayout(self._sub_right_layout)

        self.plot_widget = QtWidgets.QWidget()
        self.plot_widget.setLayout(self._main_layout)
        self.plot_widget.closeEvent = self.closeEvent
        self.plot_widget.resize(1000, 600)

    def _configuration(self):
        widget = self._build_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(widget, self.attr['TYPE'])
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _export_data(self):
        pass

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message):
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Scan Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in self.attr.items()
        ]))
        # ====================================================================

        from scipy.interpolate import griddata
        int_data = self.data
        w, h = int_data.shape

        try:
            tth = self.attr['two_theta_data'][0]
        except KeyError:
            tth = self.attr.get('TWOTHETA')

        try:
            omega = self.attr.get('OMEGA')
        except KeyError:
            omega = self.attr['omega_data']
        try:
            phi = self.attr['phi_data'][0]
        except KeyError:
            phi = self.attr['PHI']

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
        s_mod = 2. / LAMBDA * np.sin(np.radians(tth / 2.))
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
            norm=LogNorm(vmin=int_data.min() + 1, vmax=int_data.max()),
            extent=[s_x.min(), s_x.max(),
                    s_z.min(), s_z.max()])

        cb = self.figure.colorbar(
            im,
            format="%.e",
            extend='max',
            ticks=np.logspace(1, np.log10(int_data.max()),
                              np.log10(int_data.max())),
        )
        cb.set_label(r'$Intensity\ (Counts\ per\ second)$', fontsize=12)

        self.xi = xi
        self.yi = yi
        self.zi = zi

        self.canvas.draw()

    def plot(self):
        """Plot Image."""
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

    @staticmethod
    def _fill_array(array):
        return np.asanyarray([i for i in array if i is not []])

    @staticmethod
    def _int2coor(axis, ind):
        coor = int(np.argmin(np.abs(axis - ind)))

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

    def _enable_cross_select(self, event):
        if event:
            self.cid_click = self.canvas.mpl_connect(
                'button_press_event', self._select_slice_centre)
            self.cid_motion = self.canvas.mpl_connect(
                'motion_notify_event', self._mpl_on_motion)
        else:
            self.canvas.mpl_disconnect(self.cid_click)
            self.canvas.mpl_disconnect(self.cid_motion)

    def _select_slice_centre(self, event):
        """Plot the line and draw the profile when clicked.

        Double click for cross_line, single click for ab_line."""
        if event.inaxes != self.figure.axes[0]:
            return

        if event.button == 1 and event.dblclick:
            self._clean_lines()
            self._cur_centre = [(event.xdata, event.ydata)]
            lines, data = self._slice_cross_area(self._cur_centre, 0.05)
            self.canvas.draw()
            self._lines.extend(lines)

            self._x_slice.set_data(data[0], {'STEPPING_DRIVE1': 'Qx'})
            self._x_slice.figure.clf()
            self._x_slice._repaint("")

            self._y_slice.set_data(data[1], {'STEPPING_DRIVE1': 'Qz'})
            self._y_slice.figure.clf()
            self._y_slice._repaint("")

        elif event.button == 1 and not event.dblclick:
            pass
            # self._count += 1
            # if self._count % 2 == 1:
            #     self._cur_centre = [(event.xdata, event.ydata)]
            # else:
            #     self._cur_centre.append((event.xdata, event.ydata))
            #     self.plot_cut(self._cur_centre, self._width)
    # Config Menu.

    def _slice_cross_area(self, event, width):
        try:
            xi = self.xi
            yi = self.yi
            s_data = self.zi
        except AttributeError:
            return

        (x_dt, y_dt) = event[0]
        x_min_dt = x_dt - width / 2
        y_min_dt = y_dt - width / 2
        x_max_dt = x_dt + width / 2
        y_max_dt = y_dt + width / 2

        [x, x_min, x_max] = [
            self._int2coor(xi, i) for i in [x_dt, x_min_dt, x_max_dt]]
        [y, y_min, y_max] = [
            self._int2coor(yi, i) for i in [y_dt, y_min_dt, y_max_dt]]

        h_lines, = plt.plot([x_min_dt, x_max_dt, x_max_dt, x_min_dt, x_min_dt],
                            [yi.min(), yi.min(), yi.max(), yi.max(), yi.min()])

        v_lines, = plt.plot([xi.min(), xi.min(), xi.max(), xi.max(), xi.min()],
                            [y_max_dt, y_min_dt, y_min_dt, y_max_dt, y_max_dt])

        if width < 1e-10:
            data_x = s_data[y, :]
            data_y = s_data[:, x]
        else:
            data_x = np.sum(s_data[y_min:y_max, :], axis=0)
            data_y = np.sum(s_data[:, x_min:x_max], axis=1)

        self.canvas.draw()
        data = [np.vstack((yi, data_y)), np.vstack((xi, data_x))]
        lines = [h_lines, v_lines]

        return lines, data,

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
    # External methods.
