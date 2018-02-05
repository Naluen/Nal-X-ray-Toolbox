import abc
import logging
from functools import partial

import numpy
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib import pyplot as plt

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
    def __init__(self):
        super(ProcModule, self).__init__()
        self.param = {}

        self.data = None
        self.attr = None

        self.plot_widget = QtWidgets.QWidget()

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

    @abc.abstractmethod
    def _build_plot_widget(self):
        pass

    @abc.abstractmethod
    def _configuration(self):
        pass

    def _configuration_close(self, event):
        self._repaint("")
        event.accept()

    @abc.abstractmethod
    def _export_data(self):
        pass

    @abc.abstractmethod
    def _repaint(self, msg):
        pass

    def _save_image(self):
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

    @abc.abstractmethod
    def plot(self):
        self.figure.clf()
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

    def set_data(self, data, attr, *arg, **kwargs):
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
            parent._save_image,
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


