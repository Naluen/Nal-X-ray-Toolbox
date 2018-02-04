import logging
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.colors import LogNorm

from module.Module import ProcModule, BasicToolBar
from module.RawFile import RawFile
from module.OneDScanProc import OneDScanProc

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


class PolesFigureProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)

    def __init__(self):
        super(PolesFigureProc, self).__init__()

        self.figure = plt.figure()

        self.param = OrderedDict([
            ('ADVANCED_SELECTION', False),
            ('V_MIN', "10"),
            ('V_MAX', "1000"),
            ('THICKNESS', "900"),
            ('SQUARE_SX', "16"),
            ('SQUARE_SY', "16"),
            ('PHI_OFFSET', "0"),
            ('BEAM_INT', "100000"),
        ])

        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "PolesFigure",

    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self._toolbar = BasicToolBar(self)
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/search.png')),
            "Auto search peak...",
            self._pk_search,
        )
        self._toolbar.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/vertical-alignment.png')),
            "Horizontal align...",
            self._int2fraction,
        )

        self.plot_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self._toolbar)
        self.layout.addWidget(self.canvas)
        self.plot_widget.setLayout(self.layout)
        self.plot_widget.resize(1000, 400)
        self.plot_widget.closeEvent = self.closeEvent

        self.refresh_canvas.connect(self._repaint)

    def _build_config_widget(self):
        config_widget = QtWidgets.QWidget(self.plot_widget)
        config_layout = QtWidgets.QVBoxLayout()
        config_widget.setLayout(config_layout)

        advanced_selection_q_radio_button = QtWidgets.QRadioButton(
            "Use Advanced Selection")
        advanced_selection_q_radio_button.setChecked(
            self.param["ADVANCED_SELECTION"])
        advanced_selection_q_radio_button.toggled.connect(
            partial(self._upt_param, "ADVANCED_SELECTION"))

        intensity_input_layout = IntensityInputWidget(self.param)

        v_min_input_layout = QtWidgets.QVBoxLayout()
        v_min_input_layout.addWidget(QtWidgets.QLabel('Norm Minimum:'))
        v_min_line_edit = QtWidgets.QLineEdit()
        v_min_line_edit.setText(self.param['V_MIN'])
        v_min_line_edit.setInputMask("999999999")
        v_min_line_edit.textChanged.connect(
            partial(self._upt_param, "V_MIN")
        )
        v_min_input_layout.addWidget(v_min_line_edit)

        v_max_input_layout = QtWidgets.QVBoxLayout()
        v_max_input_layout.addWidget(QtWidgets.QLabel('Norm Maximum:'))
        v_max_line_edit = QtWidgets.QLineEdit()
        v_max_line_edit.setText(self.param['V_MAX'])
        v_max_line_edit.setInputMask("999999999")
        v_max_line_edit.textChanged.connect(
            partial(self._upt_param, "V_MAX")
        )
        v_max_input_layout.addWidget(v_max_line_edit)

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

        square_sx_input_layout = QtWidgets.QVBoxLayout()
        square_sx_input_layout.addWidget(
            QtWidgets.QLabel('Square Sx:'))
        square_sx_line_edit = QtWidgets.QLineEdit()
        square_sx_line_edit.setText(self.param['SQUARE_SX'])
        square_sx_line_edit.setInputMask("99")
        square_sx_line_edit.textChanged.connect(
            partial(self._upt_param, "SQUARE_SX")
        )
        square_sx_input_layout.addWidget(square_sx_line_edit)

        square_sy_input_layout = QtWidgets.QVBoxLayout()
        square_sy_input_layout.addWidget(
            QtWidgets.QLabel('Square Sy:'))
        square_sy_line_edit = QtWidgets.QLineEdit()
        square_sy_line_edit.setText(self.param['SQUARE_SY'])
        square_sy_line_edit.setInputMask("99")
        square_sy_line_edit.textChanged.connect(
            partial(self._upt_param, "SQUARE_SY")
        )
        square_sy_input_layout.addWidget(square_sy_line_edit)

        phi_offset_input_layout = QtWidgets.QVBoxLayout()
        phi_offset_input_layout.addWidget(
            QtWidgets.QLabel('Square Sx:'))
        phi_offset_line_edit = QtWidgets.QLineEdit()
        phi_offset_line_edit.setText(self.param['PHI_OFFSET'])
        phi_offset_line_edit.setValidator(
            QtGui.QIntValidator(0, 360, phi_offset_line_edit))
        phi_offset_line_edit.textChanged.connect(
            partial(self._upt_param, 'PHI_OFFSET')
        )
        phi_offset_input_layout.addWidget(phi_offset_line_edit)


        config_layout.addWidget(advanced_selection_q_radio_button)
        config_layout.addLayout(intensity_input_layout)
        config_layout.addLayout(v_min_input_layout)
        config_layout.addLayout(v_max_input_layout)
        config_layout.addLayout(thickness_input_layout)
        config_layout.addLayout(square_sx_input_layout)
        config_layout.addLayout(square_sy_input_layout)
        config_layout.addLayout(phi_offset_input_layout)

        return config_widget

    def _configuration(self):

        self._configuration_wd = self._build_config_widget()

        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(self._configuration_wd, "Poles Figure")
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _export_data(self):
        pass

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message):
        self.figure.clf()
        try:
            v_max = self.attr['V_MAX']
            v_min = self.attr['V_MIN']
        except KeyError:
            v_min = 10
            v_max = 10000
        try:
            ver_min = int(self.attr['DRV_2'].min())
            ver_max = int(self.attr['DRV_2'].max())
            hor_min = int(self.attr['DRV_1'].min())
            hor_max = int(self.attr['DRV_1'].max())
        except KeyError:
            ver_min = np.int64(self.attr['phi_min'])
            ver_max = np.int64(self.attr['phi_max'])
            hor_min = np.int64(self.attr['khi_min'])
            hor_max = np.int64(self.attr['khi_max'])
        plt.figure(self.figure.number)
        ax2d = plt.gca()
        im = ax2d.imshow(
            self.data,
            origin="lower",
            norm=LogNorm(vmin=v_min, vmax=v_max),
            extent=[ver_min, ver_max, hor_min, hor_max]
        )

        ax2d.tick_params(axis='both', which='major', labelsize=10)
        plt.colorbar(
            im,
            # fraction=0.012,
            # pad=0.04,
            format="%.e", extend='max',
            ticks=np.logspace(1, np.log10(v_max), np.log10(v_max)),
            orientation='horizontal',
        )

        self.canvas.draw()

    # External methods.
    def plot(self):
        """Plot Image."""
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

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

    # Canvas Event
    def _on_press(self, event):
        ax_list = self.figure.axes
        self._selected_square = []
        # If square have not been added, return
        if (not hasattr(self, 'res')) or len(self.res) < 3:
            return
        if event.inaxes != ax_list[0]:
            return
        for square in self.res[2]:
            if [event.xdata, event.ydata] in square:
                self._selected_square.append(square)

    def _on_motion(self, event):
        if not hasattr(self, '_selected_square'):
            return
        if event.inaxes != self.figure.gca():
            return
        [init_mouse_x, init_mouse_y] = self._selected_square[0].cr_l
        for square in self._selected_square:
            dx = event.xdata - init_mouse_x + 30
            dy = event.ydata - init_mouse_y
            square.move((dx, dy))

        self.canvas.draw()

    def _on_release(self, event):
        # If square have not been added, return
        if (not hasattr(self, 'res')) or len(self.res) < 3:
            return
        # Clear selected items.
        del self._selected_square

        outer_index_list = [i.cr_l for i in self.res[2][:4]]
        self._sq_pk_integrate(
            repaint=False,
            outer_index_list=outer_index_list
        )

    # Peak Detection.
    def _pk_search(self):
        try:
            is_advanced = self.param['ADVANCED_SELECTION']
        except KeyError:
            is_advanced = self.param['Advanced Selection']
        if is_advanced:
            self.res = self._poly_pk_integrate()
        else:
            self.res = self._sq_pk_integrate()


    def _poly_pk_integrate(self, repaint=True):
        """
        Integrate Peak intensity with polygon method.
        :param
        repaint: if re-draw the canvas.
        :return:
        int_vsot_bg_m: The intensity of the peak without background 1*4 matrix
        ind_l: The middle position of square. Same format as outer_index_list.
            Format: [[chi1, phi1], [chi2, phi2], [chi3, phi3], [chi4, phi4]]
        """
        from scipy.ndimage.filters import gaussian_filter
        from skimage import img_as_float
        from skimage.morphology import reconstruction
        from skimage.measure import label, regionprops
        from skimage.filters import threshold_niblack
        from skimage.segmentation import clear_border
        from skimage.morphology import closing, square
        from skimage import feature

        n, bins = np.histogram(
            self.data.ravel(),
            bins=int(self.data.max() - self.data.min()),
        )
        bk_int = bins[np.argmax(n)]

        image = img_as_float(self.data)
        try:
            ver_min = int(self.attr['DRV_2'].min())
            ver_max = int(self.attr['DRV_2'].max())
            hor_min = int(self.attr['DRV_1'].min())
            hor_max = int(self.attr['DRV_1'].max())
        except KeyError:
            ver_min = np.int64(self.attr['phi_min'])
            ver_max = np.int64(self.attr['phi_max'])
            hor_min = np.int64(self.attr['khi_min'])
            hor_max = np.int64(self.attr['khi_max'])

        image = gaussian_filter(image, 1, mode='nearest')

        h = 0.2
        seed = image - h
        mask = image
        # Dilate image to remove noise.
        dilated = reconstruction(seed, mask, method='dilation')
        # Use local threshold to identify all the close area.
        thresh = threshold_niblack(dilated, window_size=27, k=0.05)
        # Select large closed area.
        bw = closing(image > thresh, square(3))
        # Remove area connected to bord.
        cleared = clear_border(bw)
        # label area.
        label_image = label(cleared)

        l, w = image.shape
        binary_img = np.zeros(shape=(l, w))
        int_vsot_bg_m = []
        ind_l = []
        for i in regionprops(label_image, self.data):
            if i.area >= 100:
                for k in i.coords:
                    binary_img[k[0], k[1] + ver_min] = 1
                int_vsot_bg_m.append(
                    np.sum(i.intensity_image) - i.area * bk_int)
                ind_l.append(i.weighted_centroid)
        int_vsot_bg_m = np.asarray(int_vsot_bg_m)

        # Draw edge of peaks.
        edges2 = feature.canny(binary_img, sigma=2)  # Find the edge.
        edge = np.full([l, w], np.nan)  # Create new image and fill with nan.
        edge[np.where(edges2 > 1e-2)] = 1  # Set edge to 1.

        plt.figure(self.figure.number)
        self._repaint(True)
        plt.imshow(
            np.roll(np.roll(edge, -hor_min, axis=0), -ver_min, axis=1),
            origin='lower',
            cmap=plt.get_cmap('binary'),
            extent=[ver_min, ver_max, hor_min, hor_max]
        )
        if repaint:
            self.canvas.draw()
        return int_vsot_bg_m, ind_l

    def _sq_pk_integrate(self, repaint=True, **kwargs):
        """
        Integrate Peak intensity with square method.
        :param
        repaint: if re-draw the canvas.
        param(optional):
            :outer_index_list: The middle position of square. Used for set up
             Square manually.
             Format: [[chi1, phi1], [chi2, phi2], [chi3, phi3], [chi4, phi4]]

        :return:
        int_vsot_bg_m: The intensity of the peak without background 1*4 matrix
        ind_l: The middle position of square. Same format as outer_index_list.
        sq_ins_l: The square plot handle.
        """
        int_data = self.data
        try:
            ver_min = np.int64(self.attr['phi_min'])
            hor_min = np.int64(self.attr['khi_min'])
            sq_sz_l = [int(self.param['Square Sx']),
                       int(self.param['Square Sy'])]
        except KeyError:
            ver_min = int(self.attr['DRV_2'].min())
            hor_min = int(self.attr['DRV_1'].min())
            sq_sz_l = [int(self.param['SQUARE_SX']),
                       int(self.param['SQUARE_SY'])]


        if 'outer_index_list' in kwargs:
            ind_l = kwargs['outer_index_list']
        else:
            ind_l = self._sq_pk_search()
        # Create Square instances.
        in_sq_l = [
            Square(
                i,
                sq_sz_l,
                int_m=int_data,
                lm_t=(ver_min, hor_min),
                color='C3',
            )
            for i in ind_l
        ]
        ot_sq_l = [
            Square(
                i,
                [i + 4 for i in sq_sz_l],
                int_m=int_data,
                lm_t=(ver_min, hor_min),
                color='C1',
            )
            for i in ind_l
        ]
        # Draw squares.
        if repaint:
            [i.plot() for i in in_sq_l]
            [i.plot() for i in ot_sq_l]

        logging.debug("Square size - {0}".format(sq_sz_l))
        logging.debug("Square centre - {0}".format(ind_l))
        int_vsot_bg_m = np.asarray([i - k for (i, k) in zip(in_sq_l, ot_sq_l)])
        sq_ins_l = in_sq_l + ot_sq_l
        if repaint:
            self.canvas.draw()

        try:
            self.canvas.mpl_disconnect(self.cid_press)
            self.canvas.mpl_disconnect(self.cid_release)
            self.canvas.mpl_disconnect(self.cid_motion)
        except AttributeError:
            pass

        self.cid_press = self.canvas.mpl_connect(
            'button_press_event', self._on_press
        )
        self.cid_release = self.canvas.mpl_connect(
            'button_release_event', self._on_release
        )
        self.cid_motion = self.canvas.mpl_connect(
            'motion_notify_event', self._on_motion
        )

        return int_vsot_bg_m, ind_l, sq_ins_l

    def _sq_pk_search(self):
        from scipy.ndimage.filters import gaussian_filter, maximum_filter
        from scipy.ndimage.morphology import generate_binary_structure

        def sort_index_list(index_list):
            """
            Sort index list to fit ABCD micro-Twins, where chi of A is max.
            :param index_list: list for each point with form [chi, khi]
            :return: sorted list.
            """
            phi_sorted_l = sorted(index_list, key=lambda pair: pair[0])
            chi_index_list = [l[1] for l in phi_sorted_l]
            shifted_index_int = chi_index_list.index(max(chi_index_list))
            from collections import deque
            phi_deque = deque(phi_sorted_l)
            phi_deque.rotate(-shifted_index_int)
            sorted_index_list = list(phi_deque)

            logging.debug("index list before sort:{0}".format(index_list))
            logging.debug(
                "index list after sort:{0}".format(sorted_index_list)
            )
            return sorted_index_list

        int_data_m = self.data
        try:
            ver_min = np.int64(self.attr['phi_min'])
            hor_min = np.int64(self.attr['khi_min'])

        except KeyError:
            ver_min = int(self.attr['DRV_2'].min())
            hor_min = int(self.attr['DRV_1'].min())

        neighborhood = generate_binary_structure(2, 2)
        for i in range(3):
            int_data_m = gaussian_filter(int_data_m, 4, mode='nearest')
        local_max = (
                maximum_filter(int_data_m,
                               footprint=neighborhood) == int_data_m
        )
        index = np.asarray(np.where(local_max))
        ft_index_list = [[i, j] for (i, j) in zip(index[1, :], index[0, :])]

        chi_threshold = 40
        ft_index_list = [i for i in ft_index_list if i[1] < chi_threshold]

        in_sq_l = [
            Square(i, [10, 10], int_data_m, (ver_min, hor_min))
            for i in ft_index_list
        ]
        ot_sq_l = [
            Square(i, [20, 20], int_data_m, (ver_min, hor_min))
            for i in ft_index_list
        ]

        int_list = [k - i for (i, k) in zip(in_sq_l, ot_sq_l)]
        ft_index_list = [
                            x for (y, x)
                            in sorted(zip(int_list, ft_index_list),
                                      key=lambda pair: pair[0])
                        ][-4:]
        ft_index_list = sort_index_list(ft_index_list)

        return ft_index_list

    # Intensity to volume fraction

    def _int2fraction(self):
        """
        Change the peak intensity to volume fraction.
        """
        if (not hasattr(self, 'res')) or len(self.res) < 2:
            return
        int_vsot_bg_m = self.res[0]
        ind_l = self.res[1]

        if not hasattr(self, 'q_dialog'):
            self.q_dialog = self._fraction_calculation_param_dialog()
        self.q_dialog.exec_()
        try:
            th = int(self.param['Thickness of sample'])
            bm_int = int(self.param['Beam Int'])
            v = abs(float(self.attr['vit_ang']))
        except KeyError:
            th = int(self.param['THICKNESS'])
            bm_int = float(self.param['BEAM_INT'])
            v = abs(float(self.attr['VIT_ANGLE']))
        omega = [
            (np.pi / 2 - np.arccos(
                np.cos(np.deg2rad(chi[1])) * np.sin(np.deg2rad(14.22))))
            for chi in ind_l]
        i_theo_l = [
            self.i_theory(bm_int, v, i, i, th, 1) for i in omega]

        volume_fraction_matrix = int_vsot_bg_m / i_theo_l * 100

        self._show_res_wd = self._res_dialog(
            int_vsot_bg_m,
            volume_fraction_matrix
        )
        self._show_res_wd.show()

        logging.debug("Beam Intensity is {0}".format(bm_int))
        logging.debug("Sample th is {0}\n".format(th))
        logging.debug("Peak intensity is {0}".format(volume_fraction_matrix))

    def _fraction_calculation_param_dialog(self):
        q_dialog = QtWidgets.QDialog()

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

        intensity_input_layout = IntensityInputWidget(self.param)

        q_push_button = QtWidgets.QPushButton("OK")
        q_push_button.clicked.connect(q_dialog.close)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(thickness_input_layout)
        layout.addLayout(intensity_input_layout)
        layout.addWidget(q_push_button)

        q_dialog.setLayout(layout)

        return q_dialog

    def _res_dialog(self, int_vsot_bg_m, volume_fraction_matrix):
        def _save2csv(int_list, fraction_list):
            """Save data to csv file.

            :param int_list: List contains intensity of peaks
            :param fraction_list: List contains volume fraction of peaks.
            :return: Csv file name.
            """
            file_name = QtWidgets.QFileDialog.getSaveFileName(
                caption='Save to csv file...',
                directory="/",
                filter="Comma-separated values file (*.csv)"
            )
            file_name = str(file_name[0])
            if not file_name:
                return
            import csv
            with open(file_name, 'w') as fp:
                spam_writer = csv.writer(fp, dialect='excel', delimiter=";")
                spam_writer.writerow(
                    ["", 'MT-A', 'MT-D', 'MT-C', 'MT-B', 'MT'])
                spam_writer.writerow(["Intensity"] + int_list)
                spam_writer.writerow(["Volume fraction"] + fraction_list)

            return file_name,

        q_table = QtWidgets.QTableWidget()
        q_table.resize(700, 200)
        q_table.setColumnCount(5)
        q_table.setRowCount(2)
        q_table.setHorizontalHeaderLabels(
            ['MT-A', 'MT-D', 'MT-C', 'MT-B', 'MT'])
        q_table.setVerticalHeaderLabels(
            ["Abs int", "Volume Fraction(%)"])

        i_l = list(int_vsot_bg_m.tolist())
        i_l.append(np.sum(int_vsot_bg_m))
        i_l = list(map(partial(round, ndigits=2), i_l))
        for i in range(len(i_l)):
            q_table.setItem(
                0, i,
                QtWidgets.QTableWidgetItem(str(i_l[i]))
            )

        f_l = list(volume_fraction_matrix.tolist())
        f_l.append(np.sum(volume_fraction_matrix))
        f_l = list(map(partial(round, ndigits=2), f_l))
        for i in range(len(f_l)):
            q_table.setItem(
                1, i,
                QtWidgets.QTableWidgetItem(str(f_l[i]))
            )

        q_table.resizeColumnsToContents()
        q_table.resizeRowsToContents()

        # Save to Csv Button
        _save2csv_button = QtWidgets.QPushButton("Save to Csv...")
        _save2csv_button.clicked.connect(lambda: _save2csv(i_l, f_l))
        # Button Group sub layout
        _show_res_wd_sub_layout = QtWidgets.QHBoxLayout()
        _show_res_wd_sub_layout.addWidget(
            _save2csv_button, alignment=QtCore.Qt.AlignRight)
        # Main layout
        _show_res_wd_layout = QtWidgets.QVBoxLayout()
        _show_res_wd_layout.addWidget(q_table)
        _show_res_wd_layout.addLayout(_show_res_wd_sub_layout)
        # Main widget
        _show_res_wd = QtWidgets.QWidget()
        _show_res_wd.setLayout(_show_res_wd_layout)
        # Resize
        w = 140
        for i in range(q_table.columnCount()):
            w += q_table.columnWidth(i)
        h = 76
        for i in range(q_table.rowCount()):
            h += q_table.rowHeight(i)
        _show_res_wd.resize(w, h)

        return _show_res_wd

class Square(object):
    def __init__(
            self,
            cr_l,
            sz_t,
            int_m=None,
            lm_t=(0, 0),
            color='b',
    ):
        self.cr_l = cr_l
        self.sz_t = sz_t
        self.int_m = int_m
        self.lm_t = lm_t
        self.color = color
        self._fh = None

    def lim(self):
        if self.int_m is None:
            x_min = self.cr_l[0] - self.sz_t[0] / 2
            x_max = self.cr_l[0] + self.sz_t[0] / 2
            y_min = self.cr_l[1] - self.sz_t[1] / 2
            y_max = self.cr_l[1] + self.sz_t[1] / 2
        else:
            w, h = self.int_m.shape
            x_min = max(0, int(np.floor(self.cr_l[0] - self.sz_t[0] / 2)))
            x_max = min(int(np.floor(self.cr_l[0] + self.sz_t[0] / 2)), h)
            y_min = max(0, int(np.floor(self.cr_l[1] - self.sz_t[1] / 2)))
            y_max = min(int(np.floor(self.cr_l[1] + self.sz_t[1] / 2)), w)

        return x_min, x_max, y_min, y_max

    def plot(self, **kwargs):
        from matplotlib.patches import Rectangle
        x_min, x_max, y_min, y_max = self.lim()
        (x_lmt, y_lmt) = self.lm_t
        self._fh = plt.gca().add_patch(
            Rectangle(
                xy=(x_min + x_lmt, y_min + y_lmt),
                width=x_max - x_min,
                height=y_max - y_min,
                linewidth=1,
                fill=False,
                color=self.color,
                **kwargs
            )
        )

    def move(self, direction_tuple):
        self.remove()
        self.cr_l = [i + j for (i, j) in zip(self.cr_l, list(direction_tuple))]
        self.plot()

    @property
    def intensity_image(self):
        x_min, x_max, y_min, y_max = self.lim()
        if self.int_m is None:
            raise AttributeError("Need intensity matrix.")
        intensity_result_matrix = self.int_m[y_min:y_max, x_min:x_max]
        peak_intensity_int = np.sum(intensity_result_matrix)

        return peak_intensity_int

    @property
    def points(self):
        x_min, x_max, y_min, y_max = self.lim()

        return (y_max - y_min) * (x_max - x_min)

    def remove(self):
        """
        Remove the the square _lines.
        :return: None
        """
        try:
            self._fh.remove()
        except ValueError as e:
            logging.debug(str(e))
            logging.debug("Could not find the square.")

    def __sub__(self, x):
        if isinstance(x, Square):
            pk_int = self.intensity_image
            pk_pt = self.points
            x_pk_int = x.intensity_image
            x_pk_pt = x.points
            bg_noise_float = (pk_int - x_pk_int) / (pk_pt - x_pk_pt)

            return pk_int - pk_pt * bg_noise_float
        else:
            return NotImplemented

    def __contains__(self, item):
        """
        Check if the point is in the square.
        :param item: the position of point [x,y].
        :return: The boolean value.
        """
        x_min, x_max, y_min, y_max = self.lim()
        (x_limit, y_limit) = self.lm_t
        if (
                x_min + x_limit < item[0] < x_max + x_limit and
                y_min + y_limit < item[1] < y_max + y_limit):
            return True
        else:
            return False

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
