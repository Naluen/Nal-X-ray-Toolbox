import abc
import io
import logging
import os
from functools import partial

import numpy
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)


class Module(QtCore.QObject):
    send_param = QtCore.pyqtSignal(dict)
    update_gui_cfg = QtCore.pyqtSignal(dict)

    # To update the config dict which control the widget UI of this processor.

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
                qline = QtWidgets.QLineEdit(str(self.param[i]))
                qline.textChanged.connect(partial(self._upt_param, i))
                sub_layout.addWidget(qline)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            else:
                pass

        widget.setLayout(layout)

        return widget

    def _upt_param(self, key='', value=''):
        logging.info("{0}: {1}".format(key, value))
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
    def get_data(self):
        na = numpy.array([])
        return na

    def get_file(self, file):
        self.file = file


class ProcModule(Module):
    """
    This class is the basic class for all the processors, which is used to
    transform the data nd-arrays into the readable images.

    Each processor should provide a GUI widget to communicate with users.

    Each child class of this should correspond to one or several kinds of scan,
    for example, the PolesFigureProc corresponds to the PF.
    """
    CUR = ''

    def __init__(self, *args):
        super(ProcModule, self).__init__()
        self.param = {}

        self.data = None
        self.attr = None

        self.plot_widget = QtWidgets.QWidget()
        self.plot_widget.setWindowTitle(args[0] if len(args) > 0 else "")

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
        >>> hkl_d = {i: ProcModule().bragg_angle_cal(0.54505, i) for i in hkl_l}
        >>> assert abs(hkl_d[(0, 0, 2)]-32.8) < 0.1
        """
        LAMBDA = 0.154055911278

        rms = lambda x: np.sqrt(np.sum(np.asarray(x) ** 2))
        bragg_angle = np.arcsin(
            LAMBDA / (2 * lattice / rms(xtal_hkl))
        )

        return np.rad2deg(bragg_angle) * 2

    def closeEvent(self, event):
        self.attr.update(self.param)
        self.send_param.emit(dict(self.attr))
        event.accept()

    def _build_plot_widget(self):
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Expanding)

        self._toolbar = BasicToolBar(self)

        "Status Bar"
        self._status_bar = QtWidgets.QStatusBar()

    @abc.abstractmethod
    def _configuration(self):
        pass

    def _configuration_close(self, event):
        self.repaint("")
        event.accept()

    def _export_data(self):
        data_file_name = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QFileDialog(),
            'Save Image file',
            "/",
            "Npz files (*.npz);;Txt File (*.txt)"
        )
        data_file_name = data_file_name[0]
        if not data_file_name:
            return

        _, file_extension = os.path.splitext(data_file_name)

        if file_extension.lower() == '.txt':
            self._export_data2txt(data_file_name)
        elif file_extension.lower() == '.npz':
            self._export_data2npz(data_file_name)
        else:
            raise TypeError()

    def _export_data2txt(self, data_file_name):
        with open(data_file_name, 'w') as file_handle:
            file_handle.write("x, y, intensity" + os.linesep)
            zi = self.data.copy()
            xi = self.xi.copy()
            yi = self.yi.copy()

            zi = zi.copy().flatten()
            xx, yy = np.meshgrid(xi, yi)
            xi = xx.flatten()
            yi = yy.flatten()
            for i, j, k in zip(xi, yi, zi):
                file_handle.write("{0}, {1}, {2}".format(i, j, k) + os.linesep)

    def _export_data2npz(self, data_file_name):
        zi = self.data.copy()
        xi = self.xi.copy()
        yi = self.yi.copy()
        np.savez(
            data_file_name,
            x=xi,
            y=yi,
            z=zi
        )

    @abc.abstractmethod
    def repaint(self, msg):
        pass

    def save_image(self):
        plt.figure(self.figure.number)
        tp_d = self.figure.canvas.get_supported_filetypes()
        filter_s = ";;".join(["{0} (*.{1})".format(tp_d[i], i) for i in tp_d])

        default_dir = self.CUR or '/'
        file_n = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QFileDialog(),
            caption="Save File...",
            directory=default_dir,
            filter=filter_s,
        )
        default_dpi = 400
        if file_n:
            try:
                plt.savefig(
                    file_n[0],
                    transparent=True,
                    dpi=default_dpi,
                    bbox_inches='tight',
                )
            except MemoryError:
                plt.savefig(
                    file_n[0],
                    transparent=True,
                    dpi=default_dpi - 100,
                    bbox_inches='tight',
                )
            self.CUR = os.path.dirname(file_n[0])
        else:
            pass

    def save_to_clipboard(self):
        plt.figure(self.figure.number)
        buf = io.BytesIO()
        plt.savefig(buf)
        QtWidgets.QApplication.clipboard().setImage(
            QtGui.QImage.fromData(buf.getvalue()))
        buf.close()

    @abc.abstractmethod
    def plot(self):
        self.figure.clf()
        self.repaint("")

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr, *args, **kwargs):
        self.data = data[()]
        self.attr = dict(attr)
        for i in self.param:
            if i in self.attr:
                self.param[i] = self.attr[i]

        return self


class BasicToolBar(QtWidgets.QToolBar):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setMinimumHeight(30)

        self.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/save.png')),
            "Save Image...",
            parent.save_image,
        )
        self.addAction(
            "Save to Clipboard",
            parent.save_to_clipboard,
        )
        self.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/export_data.png')),
            "Export Data...",
            parent._export_data,
        )
        self.addAction(
            QtGui.QIcon(QtGui.QPixmap('icons/settings.png')),
            "Configuration...",
            parent._configuration,
        )
        self.addSeparator()
