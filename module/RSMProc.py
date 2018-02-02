import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm
from PyQt5 import QtCore, QtGui, QtWidgets

from module.Module import ProcModule

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

    rms = lambda x: np.sqrt(np.sum(np.asarray(x)**2))
    bragg_angle = np.arcsin(LAMBDA / (2 * lattice / rms(xtal_hkl)))

    return np.rad2deg(bragg_angle) * 2


class RSMProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(RSMProc, self).__init__()
        self.param = {}
        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "RMS",

    @staticmethod
    def _fill_array(array):
        return np.asanyarray([i for i in array if i is not []])

    # Build Canvas
    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Expanding)

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
        self.plot_widget.resize(1000, 400)

        self.refresh_canvas.connect(self._repaint)

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
            self.attr['omega_data']
        try:
            phi = self.attr['phi_data'][0]
        except KeyError:
            phi = self.attr['PHI']

        hkl_l = [(0, 0, 2), (0, 0, 4), (0, 0, 6), (2, 2, -4)]
        hkl_d = {i: _bragg_angle_cal(LATTICE_GAP, i) for i in hkl_l}
        logging.debug(tth)
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
        im = plt.imshow(
            zi,
            origin='lower',
            norm=LogNorm(vmin=int_data.min() + 1, vmax=int_data.max()),
            extent=[s_x.min(), s_x.max(),
                    s_z.min(), s_z.max()])

        cb = plt.colorbar(
            im,
            format="%.e",
            extend='max',
            ticks=np.logspace(1, np.log10(int_data.max()),
                              np.log10(int_data.max())),
        )
        cb.set_label(r'$Intensity\ (Counts\ per\ second)$', fontsize=12)

        self._data_dict = {}
        self._data_dict['xi'] = xi
        self._data_dict['yi'] = yi
        self._data_dict['s_data'] = zi

        self.canvas.draw()

    # Config Menu.
    def _configuration(self):
        widget = self._build_widget()
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(widget, self.attr['TYPE'])
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _close_configuration(self, event):
        self.refresh_canvas.emit(True)
        event.accept()

    # External methods.
    def plot(self):
        """Plot Image."""
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget
