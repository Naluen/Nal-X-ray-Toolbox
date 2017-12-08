import abc
import logging

import numpy
from PyQt5 import QtCore, QtWidgets
from matplotlib import pyplot as plt

from functools import partial


class Module(QtCore.QObject):
    send_param = QtCore.pyqtSignal(dict)

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
                qradiobox.toggled.connect(partial(self.param.__setitem__, i))
                sub_layout.addWidget(qradiobox)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], str):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QVBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                qline = QtWidgets.QLineEdit(self.param[i])
                qline.textChanged.connect(partial(self.param.__setitem__, i))
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
                p_spin.valueChanged.connect(partial(self.param.__setitem__, i))
                sub_layout.addWidget(p_spin)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], (float, numpy.float_)):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QHBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                qline = QtWidgets.QLineEdit(self.param[i])
                qline.textChanged.connect(
                    lambda: self.param.update({i: float(qline.text()[0])}))
                sub_layout.addWidget(qline)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)
            elif isinstance(self.param[i], range):
                sub_widget = QtWidgets.QWidget()
                sub_layout = QtWidgets.QHBoxLayout()
                sub_layout.addWidget(QtWidgets.QLabel('{0}:'.format(i)))
                qline = QtWidgets.QLineEdit(self.param[i])
                range_keeper = (
                    lambda ind, range_l: min(max(range_l[0], ind),
                                             range_l[-1]))
                qline.textChanged.connect(
                    lambda: self.param.update(
                        {i: range_keeper(float(qline.text()[0]),
                                         self.param[i])}
                    ))
                qline.textChanged.connect(
                    lambda: qline.setText(str(
                        range_keeper(float(qline.text()[0]), self.param[i]))))
                sub_layout.addWidget(qline)
                sub_widget.setLayout(sub_layout)
                layout.addWidget(sub_widget)

            else:
                pass

        del i
        widget.setLayout(layout)

        return widget


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
    def file2narray(self):
        na = numpy.array([])
        return na

    def get_file(self, file):
        self.file = file


class ProcModule(Module):
    def __init__(self):
        super(ProcModule, self).__init__()
        self.figure = plt.figure("self")
        self.param = {}

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    @abc.abstractmethod
    def supp_type(self):
        # Supportive file type.
        # Accept str and any other type could be changed into list.
        pass

    @abc.abstractmethod
    def plot(self):
        self.figure.clf()
        self._repaint("")

        self.plot_widget.show()

        return self.plot_widget

    def _save(self):
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

    def set_data(self, data, attr):
        self.data = data[()]
        self.attr = dict(attr)
        for i in self.param:
            if i in self.attr:
                self.param[i] = self.attr[i]

    def closeEvent(self, event):
        self.attr.update(self.param)
        self.send_param.emit(dict(self.attr))
