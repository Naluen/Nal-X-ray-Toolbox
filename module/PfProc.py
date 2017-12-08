import logging
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.colors import LogNorm

from module.Module import ProcModule
from module.RawFile import RawFile


class PfProc(ProcModule):
    refresh_canvas = QtCore.pyqtSignal(bool)
    set_q_int_line_v = QtCore.pyqtSignal(int)

    def __init__(self):
        super(PfProc, self).__init__()

        self.param = OrderedDict([
            ('Advanced Selection', False),
            ('v_min', 10),
            ('v_max', 1000),
            ('Thickness of sample', 900),
            ('Square Sx', 16),
            ('Square Sy', 16),
            ('Phi offset', 0),
            ('Beam Int', 0),
        ])

        self.q_line_wd = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Beam Intensity"))
        self.q_int_line = QtWidgets.QLineEdit(str(self.param['Beam Int']))
        self.q_int_line.textChanged.connect(
            partial(self.param.__setitem__, 'Beam Int'))
        q_int_button = self.q_int_line.addAction(
            QtGui.QIcon(QtGui.QPixmap('module/icons/more.png')),
            QtWidgets.QLineEdit.TrailingPosition)
        q_int_button.triggered.connect(self._get_bm_int)
        layout.addWidget(self.q_int_line)
        self.q_line_wd.setLayout(layout)
        self.set_q_int_line_v.connect(self._set_q_int_line)

        self._build_plot_widget()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return "PolesFigure",

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

    @QtCore.pyqtSlot(int)
    def _set_q_int_line(self, msg):
        self.q_int_line.setText(str(msg))
        self.param['Beam Int'] = int(msg)

    @QtCore.pyqtSlot(bool)
    def _repaint(self, message):
        self.figure.clf()
        v_max = (
            int(self.attr['v_max'])
            if ('v_max' in self.attr and self.attr['v_max'])
            else 10
        )
        v_min = (
            int(self.attr['v_min'])
            if ('v_min' in self.attr and self.attr['v_min'])
            else 10000
        )
        ver_min = self.attr['phi_min']
        ver_max = self.attr['phi_max']
        hor_min = self.attr['khi_min']
        hor_max = self.attr['khi_max']
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

    def closeEvent(self, event):
        self.attr.update(self.param)
        self.send_param.emit(dict(self.attr))
        event.accept()

    # Build canvas
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
        self._sq_pk_int(
            repaint=False,
            outer_index_list=outer_index_list
        )

    # Config Menu
    def _configuration(self):
        _tmp = self.param['Beam Int']
        self.param.pop('Beam Int', None)

        self._configuration_wd = self._build_widget()

        self.param['Beam Int'] = _tmp

        self._configuration_wd.layout().addWidget(self.q_line_wd)
        self.q_tab_widget = QtWidgets.QTabWidget()
        self.q_tab_widget.addTab(self._configuration_wd, "Poles Figure")
        self.q_tab_widget.closeEvent = self._close_configuration
        self.q_tab_widget.show()

    def _close_configuration(self, event):
        self.refresh_canvas.emit(True)
        event.accept()

    # Peak Detection.
    def _pk_search(self):
        if self.param['Advanced Selection']:
            self.res = self._poly_pk_int()
        else:
            self.res = self._sq_pk_int()

    def _poly_pk_int(self, repaint=True):
        from scipy.ndimage.filters import gaussian_filter
        from skimage import img_as_float
        from skimage.morphology import reconstruction
        from skimage.measure import label, regionprops
        from skimage.filters import threshold_niblack
        from skimage.segmentation import clear_border
        from skimage.morphology import closing, square
        from skimage import feature

        image = img_as_float(self.data.T)
        ver_min = int(self.attr['phi_min'])
        ver_max = self.attr['phi_max']
        hor_min = self.attr['khi_min']
        hor_max = self.attr['khi_max']

        image = gaussian_filter(image, 1, mode='nearest')

        h = 0.2
        seed = image - h
        mask = image
        # Dilate image to remove noise.
        dilated = reconstruction(seed, mask, method='dilation')
        # Use local threshold to identify all the close area.
        thresh = threshold_niblack(dilated, window_size=27, k=0.05)
        bw = closing(image > thresh, square(3))
        # Remove area connected to bord.
        cleared = clear_border(bw)
        # label area.
        label_image = label(cleared)

        l, w = image.shape
        binary_img = np.zeros(shape=(l, w))
        int_vsot_bg_m = []
        ind_l = []
        for i in regionprops(label_image, self.data.T):
            if i.area >= 100:
                for k in i.coords:
                    binary_img[k[0], k[1] + ver_min] = 1
                int_vsot_bg_m.append(np.sum(i.intensity_image))
                ind_l.append(i.weighted_centroid)

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

    def _sq_pk_int(self, repaint=True, **kwargs):
        """
        Count Peak with square method.
        :param
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
        scan_dict = self.attr
        ver_min = self.attr['phi_min']
        hor_min = self.attr['khi_min']
        sq_sz_l = [int(scan_dict['Square Sx']), int(scan_dict['Square Sy'])]

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
        ver_min = self.attr['phi_min']
        hor_min = self.attr['khi_min']

        neighborhood = generate_binary_structure(2, 2)
        for i in range(3):
            int_data_m = gaussian_filter(int_data_m, 4, mode='nearest')
        local_max = (
            maximum_filter(int_data_m, footprint=neighborhood) == int_data_m
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
        :param int_vsot_bg_m: Peak intensity matrix without background.
        :param ind_l: The index list of peak positions.
        :return: THe volume fraction list of each peak.
        """
        if (not hasattr(self, 'res')) or len(self.res) < 2:
            return
        int_vsot_bg_m = self.res[0]
        ind_l = self.res[1]

        if not hasattr(self, 'q_dialog'):
            self.q_dialog = self._demand_param_fraction()
        self.q_dialog.exec_()

        thickness = int(self.param['Thickness of sample'])
        bm_int = int(self.param['Beam Int'])

        eta = [self._correction(x[0], thickness) for x in ind_l]

        logging.debug("Intensity _correction index eta is {0}".format(eta))

        coefficient_list = np.asarray([
            0.939691064,
            0.666790711 / (eta[1] / eta[0]),
            0.426843274 / (eta[2] / eta[0]),
            0.72278158 / (eta[3] / eta[0])
        ])
        volume_fraction_matrix = (
            int_vsot_bg_m * 10000 * coefficient_list / bm_int
        )

        self._show_result(int_vsot_bg_m, volume_fraction_matrix)

        logging.debug("Beam Intensity is {0}".format(bm_int))
        logging.debug("Sample thickness is {0}\n".format(thickness))
        logging.debug("Peak intensity is {0}".format(volume_fraction_matrix))

    def _demand_param_fraction(self):
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
        layout.addWidget(q_push_button)

        q_dialog.setLayout(layout)

        return q_dialog

    @staticmethod
    def _bragg_angle_cal(m, xtal_hkl):
        """
        Calculation the bragg angle based on the material and crystal miller
        index.
        :param m: Material Name
        :param xtal_hkl: Miller index
        :return: theoretical bragg angle.
        """
        # import XrdAnalysis.Materials as Matl
        # m_dict = {
        #     'gap': Matl.GaP,
        #     'si': Matl.Si,
        #     'gan': Matl.GaN
        # }

        x_ray_wv_len = 0.154056  # Cu K-alpha 1 wave length of x-ray.

        rms = lambda x: np.sqrt(np.mean(np.asarray(x) ** 2))
        bragg_angle = np.arcsin(
            x_ray_wv_len / (2 * 5.4505 / rms(xtal_hkl))
        )

        return bragg_angle

    @classmethod
    def _correction(cls, chi, thickness):
        xtal_hkl = [1, 1, 1]  # the crystal direction of scan.
        theta = cls._bragg_angle_cal('GaP', xtal_hkl)
        omega = theta
        thickness /= 1000.
        e_angle = np.pi / 2 - np.arccos(
            np.cos(np.deg2rad(chi)) * np.sin(theta))
        i_angle = np.pi / 2 - np.arccos(
            np.cos(np.deg2rad(chi)) * np.sin(omega))

        eta = 1. / 37.6152  # 1/um at 8.05keV (CXRO)
        p = np.sin(2 * e_angle - i_angle)
        q = np.sin(i_angle)
        coefficient_b = p / (p + q)
        coefficient_c = 1. - np.exp(-eta * thickness * (1. / p + 1. / q))
        coefficient = coefficient_b * (1. / eta) * coefficient_c

        logging.debug(
            "eta:{0}, thickness:{1}, p:{2}, q:{3}, c_c:{4}".format(
                eta, thickness, p, q, coefficient_c
            )
        )
        return coefficient

    def _show_result(self, int_vsot_bg_m, volume_fraction_matrix):
        q_table = QtWidgets.QTableWidget()
        q_table.resize(700, 200)
        q_table.setColumnCount(5)
        q_table.setRowCount(2)
        q_table.setHorizontalHeaderLabels(
            ['MT-A', 'MT-D', 'MT-C', 'MT-B', 'MT'])
        q_table.setVerticalHeaderLabels(
            ["Abs int", "Volume Fraction(%)"])
        i_l = int_vsot_bg_m.tolist()
        i_l.append(np.sum(int_vsot_bg_m))
        i_l = list(map(partial(round, ndigits=2), i_l))
        for i in range(len(i_l)):
            q_table.setItem(
                0, i,
                QtWidgets.QTableWidgetItem(str(i_l[i]))
            )
        f_l = volume_fraction_matrix.tolist()
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
        _save2csv_button.clicked.connect(lambda: self._save2csv(i_l, f_l))
        # Button Group sub layout
        _show_res_wd_sub_layout = QtWidgets.QHBoxLayout()
        _show_res_wd_sub_layout.addWidget(
            _save2csv_button, alignment=QtCore.Qt.AlignRight)
        # Main layout
        _show_res_wd_layout = QtWidgets.QVBoxLayout()
        _show_res_wd_layout.addWidget(q_table)
        _show_res_wd_layout.addLayout(_show_res_wd_sub_layout)
        # Main widget
        self._show_res_wd = QtWidgets.QWidget()
        self._show_res_wd.setLayout(_show_res_wd_layout)
        # Resize
        w = 140
        for i in range(q_table.columnCount()):
            w += q_table.columnWidth(i)
        h = 76
        for i in range(q_table.rowCount()):
            h += q_table.rowHeight(i)
        self._show_res_wd.resize(w, h)
        # Show Main widget
        self._show_res_wd.show()

    @staticmethod
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
            spam_writer.writerow(["", 'MT-A', 'MT-D', 'MT-C', 'MT-B', 'MT'])
            spam_writer.writerow(["Intensity"] + int_list)
            spam_writer.writerow(["Volume fraction"] + fraction_list)

        return file_name,

    # Extenal methods.
    def plot(self):
        """Plot Image."""
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr):
        self.data = data[()]
        self.attr = dict(attr)
        for i in self.param:
            if i in self.attr:
                self.param[i] = self.attr[i]
        if 'Beam Int' in self.attr:
            self.set_q_int_line_v.emit(self.attr['Beam Int'])


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
