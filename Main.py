import logging
import os
import shutil

import h5py
import numpy
import yaml
from PyQt5 import QtWidgets, QtCore

from ui.ConfirmInt.ConfirmInterface import ConfirmInterface
from ui.GUI import Ui_MainWindow
from ui.PrefInt.PreferenceInterface import PreferenceInterface
from ui.RecipeInt.InsertRecipeInterface import InsertRecipeInterface
from ui.TableInt.TableInt import TableInt

DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.join(DIR, "module")

CONFIG = os.path.join(DIR, "CFG.yml")
MODULE_G = "MODULE"
PREFERENCE = 'PREFERENCE'
GENERAL = 'GENERAL'
MAT_LIB = 'db_lib_path'


# TODO: Add search bar for recipe
# TODO: Plot recipe.

def block_tree_signal(func):
    def wrapper(self, **kw):
        self.ui.treeWidget.blockSignals(True)
        res = func(self, **kw)
        self.ui.treeWidget.blockSignals(False)
        return res

    return wrapper


class ProgramInterface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        os.chdir(DIR)

        self.f_path = ''
        self.cut_items_l = []
        self.copy_items_l = []
        with open(CONFIG, 'r') as yml_file:
            self.cfg = yaml.safe_load(yml_file)

        try:
            self._self_checker()
        except NotImplementedError as e:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(str(e))
            self._error.accepted.connect(self.close)
            self._error.rejected.connect(self.close)

        # Initiate the modules and library.
        self._init_module()
        self._init_lib()

        self.preference_inf = PreferenceInterface()
        self.preference_inf.upt_cfg.connect(self._upt_cfg)

        self.ui.treeWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.ui.treeWidget.itemChanged.connect(
            lambda: self.rename_item(self.f_path))

        self.ui.actionAdd_Module.triggered.connect(self._add_module)
        self.ui.actionImport_Data.triggered.connect(self._add_data)
        self.ui.actionDelete_Data.triggered.connect(self.delete_items)
        self.ui.actionRename.triggered.connect(self.enable_editable)
        self.ui.actionCut.triggered.connect(self.cut_items)
        self.ui.actionCopy.triggered.connect(self.copy_items)
        self.ui.actionPaste.triggered.connect(self.paste_items)
        self.ui.action_Detail.triggered.connect(self.detail_item)
        self.ui.action_Plot.triggered.connect(self.plot_item)
        self.ui.actionAdd_Group.triggered.connect(self.add_grp)

        self.ui.actionInsert_Recipe.triggered.connect(self._insert_rcp)

        self.ui.actionParameters.triggered.connect(self._open_pref)

        self.ui.treeWidget.header().close()

        # Popup menu setup for ui.treeview.
        self.ui.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.treeWidget.customContextMenuRequested.connect(
            self.tree_view_open_menu)

        timer = QtCore.QTimer()
        timer.timeout.connect(self._write_cfg)
        timer.start(300000)

    # Init and self check function.

    def _self_checker(self):
        # Check basic package(H5File) existed
        logging.info("Checking basic package...")
        # Check H5File
        with open(CONFIG, 'r') as yml_file:
            self.cfg = yaml.safe_load(yml_file)
        if MODULE_G not in self.cfg:
            self.cfg[MODULE_G] = {}
        if "H5File" not in self.cfg[MODULE_G]:
            raise NotImplementedError("H5File package is lost.")

    # Function of modules.
    def _init_module(self):
        """Init the module menu according the registered modules in config.

        :return:
        """

        for i in self.cfg[MODULE_G]:
            self.ui.menuInstalled_Module.addAction(
                QtWidgets.QAction(
                    str(self.cfg[MODULE_G][i]['name']),
                    self.ui.menuInstalled_Module
                )
            )

    def _add_module(self):
        """Add module action"""
        mdl = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open file',
            __file__,
            "Python files (*.py)")
        mdl = str(mdl[0])
        if not mdl:
            return

        # Move file to module
        mdl_n = os.path.basename(mdl)
        new_mdl = os.path.join(MODULE_DIR, mdl_n)
        try:
            shutil.copyfile(mdl, new_mdl)
        except shutil.SameFileError:
            pass

        # import module
        mdl_n = str(mdl_n.split('.')[0])
        _tmp = __import__(
            'module', globals(), locals(), [mdl_n], 0)
        _mdl = getattr(_tmp, mdl_n)
        _mdl = getattr(_mdl, mdl_n)

        # Register module to config file.
        self.cfg[MODULE_G].setdefault(mdl_n, {})
        self.cfg[MODULE_G][mdl_n].setdefault('name', _mdl().name)
        if isinstance(_mdl().supp_type, str):
            sup_tp_l = [_mdl().supp_type]
        else:
            sup_tp_l = list(_mdl().supp_type)

        for i in sup_tp_l:
            self.cfg['TYPE_DICT'][i] = mdl_n

        # Add module to menu.
        self._tmp_act = QtWidgets.QAction(mdl_n)
        self.ui.menuInstalled_Module.addAction(self._tmp_act)

    # Function of library.

    def _init_lib(self):
        """ Init the ui.QTreeWidget according to the h5 lib.

        :return:
        """

        path = 'db_path'
        lib_f = self.cfg[PREFERENCE][GENERAL][path]
        if not os.path.isfile(lib_f):
            lib_f = os.path.join(DIR, 'lib.h5')
            self.cfg[PREFERENCE][GENERAL][path] = lib_f

            h5py.File(lib_f, 'w')

        try:
            self.lib = self._get_file_reader(lib_f)
        except TypeError as e:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(str(e))
            return

        self.ui.treeWidget.clear()
        root_item = QtWidgets.QTreeWidgetItem(self.ui.treeWidget)
        root_item.setText(0, '/')

        def post_order(g, l):
            for i in l.keys():
                if hasattr(l[i], "keys"):
                    gp = QtWidgets.QTreeWidgetItem(g, [i])
                    gp.setFlags(gp.flags() | QtCore.Qt.ItemIsEditable)
                    post_order(gp, l[i])
                else:
                    item = QtWidgets.QTreeWidgetItem(g, [i])
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

        post_order(root_item, self.lib.fh)

        root_item.setExpanded(True)

        try:
            self._mat_lib = self._get_file_reader(
                self.cfg[PREFERENCE][GENERAL][MAT_LIB])
        except:
            self.cfg[PREFERENCE][GENERAL][MAT_LIB] = os.path.join(
                DIR, 'lib', 'mat.h5')
            self._mat_lib = self._get_file_reader(
                self.cfg[PREFERENCE][GENERAL][MAT_LIB])

            # self.view_sort(self.ui.treeWidget)

    def _add_data(self):
        """Menu action to import data from file.

        There will be a dialog to demand group
        :return:
        """
        raw_file_names = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open file',
            "/")
        raw_file_names = raw_file_names[0]
        if not raw_file_names:
            return
        for i in raw_file_names:
            self._save_data(str(i))
        self.lib.fh.flush()

    @block_tree_signal
    def add_grp(self):
        item = self.ui.treeWidget.currentItem()
        ch_text_l = [item.child(i).text(0) for i in range(item.childCount())]

        new_item = QtWidgets.QTreeWidgetItem(item)
        if "New Group" not in ch_text_l:
            new_item.setText(0, "New Group")
        else:
            i = 1
            while 'New Group {0}'.format(i) in ch_text_l:
                i += 1
            new_item.setText(0, 'New Group {0}'.format(i))

        new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.treeWidget.clearSelection()
        new_item.setSelected(True)
        self.ui.treeWidget.editItem(new_item, 0)

        self.f_path = self._item2h5(new_item)
        self.lib.fh.create_group(self.f_path)

    @block_tree_signal
    def delete_items(self):
        """Delete items from lib."""
        root = self.ui.treeWidget.invisibleRootItem()
        item_l = self.ui.treeWidget.selectedItems()
        self.temp_confirm = ConfirmInterface()
        self.temp_confirm.set_text(
            "Would you like to delete {0}?".format(
                *[i.text(0) for i in item_l]))
        self.temp_confirm.exec()
        if self.temp_confirm.get_bool():
            for item in item_l:
                # Delete the item from h5file.
                h5_path = self._item2h5(item)
                logging.debug("Deleting {0}...".format(h5_path))
                del self.lib.fh[h5_path]
                # Delete the item from qTreeWidget
                (item.parent() or root).removeChild(item)
        else:
            return

        del self.temp_confirm

    @block_tree_signal
    def enable_editable(self):
        item = self.ui.treeWidget.currentItem()
        self.f_path = self._item2h5(item)
        self.ui.treeWidget.editItem(item, 0)

    def rename_item(self, f_path):
        c_path = self._item2h5(self.ui.treeWidget.selectedItems()[0])
        print(c_path)
        if c_path in self.lib.fh:
            overwrite_alert = ConfirmInterface()
            overwrite_alert.set_text("Overwrite data in destiny group?")
            overwrite_alert.exec()
            if overwrite_alert.get_bool:
                root = self.ui.treeWidget.invisibleRootItem()
                item = self._h52item(c_path)
                (item.parent() or root).removeChild(item)
                del self.lib.fh[c_path]
                logging.debug(f_path + '->' + c_path)
                self.lib.fh.move(f_path, c_path)
                self.lib.fh.flush()
        else:
            self.lib.fh.move(f_path, c_path)
            self.lib.fh.flush()

    def cut_items(self):
        self.cut_items_l = []
        self.copy_items_l = []
        # Check if all the items are in the same level.
        if all(x.parent() == self.ui.treeWidget.selectedItems()[0].parent()
               for x in self.ui.treeWidget.selectedItems()):
            self.cut_items_l = self.ui.treeWidget.selectedItems()
        else:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(
                "All selected item should in the same level")
            return

    def copy_items(self):
        self.cut_items_l = []
        self.copy_items_l = []
        if all(x.parent() == self.ui.treeWidget.selectedItems()[0].parent()
               for x in self.ui.treeWidget.selectedItems()):
            self.copy_items_l = self.ui.treeWidget.selectedItems()
        else:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(
                "All selected item should in the same level")
            return

    @block_tree_signal
    def paste_items(self):
        # Check the destiny to be group.
        n_grp = self._item2h5(self.ui.treeWidget.currentItem())
        if self.lib.is_data_set(n_grp) != 1:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(
                "The destiny should be a group.")
            return
        # Cut in library
        is_in_lib = [(self._item2h5(i) in self.lib.fh)
                     for i in self.cut_items_l + self.copy_items_l]
        if any(is_in_lib):
            overwrite_alert = ConfirmInterface()
            overwrite_alert.set_text("Overwrite data in destiny group?")
            overwrite_alert.exec()
            if not overwrite_alert.get_bool:
                return
        root = self.ui.treeWidget.invisibleRootItem()
        for i in self.cut_items_l:
            f_path = self._item2h5(i)
            n_path = (n_grp + "/" + f_path.split("/")[-1])
            if n_path in self.lib.fh:
                del self.lib.fh[n_path]
            else:
                n_ch = i.clone()
                self.ui.treeWidget.currentItem().addChild(n_ch)
            self.lib.fh.move(f_path, n_path)

            (i.parent() or root).removeChild(i)
        # Copy in library
        for i in self.copy_items_l:
            f_path = self._item2h5(i)
            n_path = (n_grp + "/" + f_path.split("/")[-1])
            if n_path in self.lib.fh:
                del self.lib.fh[n_path]
            else:
                n_ch = i.clone()
                self.ui.treeWidget.currentItem().addChild(n_ch)
            self.lib.fh[n_path] = f_path

    def _save_data(self, raw_file_name):
        try:
            reader = self._get_file_reader(raw_file_name)
        except TypeError as e:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(str(e))
            return

        is_duplicate = False

        logging.debug("Recording data to h5 file...")
        h5_path = self._item2h5(self.ui.treeWidget.currentItem())
        data, attr, *_ = reader.file2narray()
        if "Type" not in attr:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage("Must set type for the data.")
            return
        name = os.path.basename(raw_file_name).split('.')[0]
        is_data = self.lib.is_data_set(h5_path)
        try:
            self.lib.set_data(
                data,
                h5_path,
                name,
                attr
            )
        except FileExistsError:
            self.temp_confirm = ConfirmInterface()
            self.temp_confirm.set_text("File has existed, overwrite?")
            self.temp_confirm.exec()
            if self.temp_confirm.get_bool():
                is_duplicate = True
                self.lib.set_data(
                    data,
                    h5_path,
                    name,
                    attr,
                    is_force=True
                )
            else:
                return
            del self.temp_confirm
        except TypeError as e:
            self._error = QtWidgets.QErrorMessage(self)
            self._error.setWindowModality(QtCore.Qt.WindowModal)
            self._error.showMessage(str(e))
            logging.warning(str(e))
            return

        # Refresh lib.
        logging.debug("Refreshing lib...")
        if is_duplicate:
            pass
        elif is_data == 0:
            QtWidgets.QTreeWidgetItem(
                self.ui.treeWidget.currentItem().parent(), [name])
        elif is_data == 1:
            QtWidgets.QTreeWidgetItem(
                self.ui.treeWidget.currentItem(), [name])
        else:
            raise IndexError

    def tree_view_open_menu(self, position):
        sub_menu = SubMenu(self)
        sub_menu.exec_(self.sender().viewport().mapToGlobal(position))

    def detail_item(self):
        self.attrInt = TableInt()
        item = self.ui.treeWidget.currentItem()
        h5_path = self._item2h5(item)
        attrs = self.lib.fh[h5_path].attrs
        attr = dict(attrs)
        logging.debug("Reading attrs: {0}".format(attr))

        self.attrInt.setWindowTitle("Attributes")

        try:
            self.attrInt.data2table(attr)
        except TypeError as e:
            logging.error(str(e))
            logging.error(type(attr))
            return

        self.attrInt.proc_done.connect(self.set_attr)
        self.attrInt.show()

    def _insert_rcp(self):
        insert_rcp_inf = InsertRecipeInterface()
        insert_rcp_inf.rcp.connect(self._add_rcp)

        mat = list(self._mat_lib.fh['semiconductor'].keys())
        key = [self._mat_lib.fh['semiconductor'][i]['print'][()] for i in mat]
        ind = [self._mat_lib.fh['semiconductor'][i]['index'][()] for i in mat]
        key = [str(x.decode("utf-8")) if isinstance(x, numpy.bytes_)
               else str(x) for _, x in sorted(zip(ind, key))
               ]

        insert_rcp_inf.set_mat(key)
        f_path = self._item2h5(self.ui.treeWidget.currentItem())
        rcp = self.lib.get_rcp(f_path)
        insert_rcp_inf.set_rcp(rcp)

        insert_rcp_inf.show()

    @QtCore.pyqtSlot(numpy.ndarray)
    def _add_rcp(self, msg):
        f_path = self._item2h5(self.ui.treeWidget.currentItem())
        self.lib.set_rcp(f_path, msg)

    @QtCore.pyqtSlot(dict)
    def set_attr(self, message):
        logging.debug(message)
        item = self.ui.treeWidget.currentItem()
        h5_path = self._item2h5(item)
        for i in message:
            self.lib.fh[h5_path].attrs[i] = message[i]
        try:
            self.attrInt.proc_done.disconnect(self.set_attr)
        except (AttributeError, TypeError):
            pass

    def plot_item(self):
        processor = self._get_data_processor(
            self.ui.treeWidget.currentItem())

        processor.send_param.connect(self.set_attr)
        processor.plot()

    # Accept drag function for main window.

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()

            for url in event.mimeData().urls():
                dropped_str = str(url.toLocalFile())
                if os.path.isdir(dropped_str):
                    for path, sub_dirs, files in os.walk(dropped_str):
                        for filename in files:
                            self._save_data(os.path.join(path, filename))
                elif os.path.isfile(dropped_str):
                    self._save_data(dropped_str)
                else:
                    self._error = QtWidgets.QErrorMessage(self)
                    self._error.setWindowModality(QtCore.Qt.WindowModal)
                    self._error.showMessage(
                        "Please choose a directory or a file.")
                    return
                self._init_lib()
        else:
            event.ignore()

    # Preference
    def _open_pref(self):
        self.preference_inf.set_config(self.cfg)
        self.preference_inf.setWindowModality(QtCore.Qt.WindowModal)
        self.preference_inf.show()

    # Pub Functions.

    def _get_file_reader(self, file):
        """Get the file reader class.

        Return: Instant with file data imported.
        """
        logging.debug("Start reading file...")
        if not isinstance(file, str):
            raise TypeError("Function only accept str type.")
        _, extension = os.path.splitext(file)
        try:
            reader_name = self.cfg['TYPE_DICT'][extension]
        except KeyError:
            raise TypeError("Unknown Type. \
            Please confirm this type is supported by at least one module.")

        _tmp = __import__('module', globals(), locals(), [reader_name], 0)

        reader = getattr(getattr(_tmp, reader_name), reader_name)()
        reader.get_file(file)

        logging.debug("Successfully read file {0}...".format(file))
        return reader

    def _get_data_processor(self, item):
        """Get the file reader class.

        Return: Instant with file data imported.
        """
        logging.debug("Start searching processor...")
        h5_path = self._item2h5(item)
        proc_type = self.lib.fh[h5_path].attrs['Type']
        if not isinstance(proc_type, str):
            raise TypeError("Function only accept str type.")
        try:
            processor = self.cfg['TYPE_DICT'][proc_type]
        except KeyError:
            print(proc_type)
            raise TypeError("Unknown Type. \
               Please confirm this type is supported by at least one module.")

        _tmp = __import__('module', globals(), locals(), [processor], 0)

        processor = getattr(getattr(_tmp, processor), processor)()
        processor.set_data(self.lib.fh[h5_path], self.lib.fh[h5_path].attrs)

        logging.debug("Successfully read file...")
        return processor

    def _get_top_item(self, item):
        """ Get the top parent item of a qTreeWidget item.

        :param item: the qTreeWidget item
        :return: the top parent item.
        """
        if item.parent():
            item = item.parent()
            self._get_top_item(item)
        return item

    @QtCore.pyqtSlot(dict, name='update_dict')
    def _upt_cfg(self, msg):
        self.cfg.update(msg)
        self._init_lib()

    def _write_cfg(self):
        with open(CONFIG, 'w') as yml_file:
            yaml.dump(self.cfg, yml_file, default_flow_style=False)

    @staticmethod
    def _item2h5(item):
        """Get the corresponding h5 path of a qTreeItem

        :param item: The qTreeItem
        :return: Corresponding h5 item path
        """
        text_l = []

        while hasattr(item, 'parent') and item.parent():
            text_l.append(item.text(0))
            item = item.parent()
        text_l.append(item.text(0))
        text_l.reverse()
        text_s = '/'.join(text_l)
        return text_s

    def _h52item(self, h5_s):
        """Get the corresponding h5 path of a qTreeItem

        :param h5: The h5 path
        :return: Corresponding qTreeItem path
        """
        text_l = h5_s.split('/')
        root = self.ui.treeWidget.invisibleRootItem()
        items = self.ui.treeWidget.findItems(
            text_l[-1],
            QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive,
            0
        )
        text_l.pop()
        for i in items:
            p_item = i.parent() or root
            if self._item2h5(p_item) == '/'.join(text_l):
                return i
            else:
                pass

    def closeEvent(self, *args, **kwargs):
        self._write_cfg()


class SubMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(SubMenu, self).__init__(parent)

        self.parent = parent

        self.addAction(parent.ui.actionRename)
        self.addAction(parent.ui.actionCut)
        self.addAction(parent.ui.actionCopy)
        self.addAction(parent.ui.actionPaste)
        self.addAction(parent.ui.actionDelete_Data)
        self.addAction(parent.ui.action_Detail)
        self.addAction(parent.ui.action_Plot)
        self.addAction(parent.ui.actionInsert_Recipe)
        self.addAction(parent.ui.actionAdd_Group)


if __name__ == '__main__':
    import sys

    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    Program = QtWidgets.QApplication(sys.argv)
    MyProgram = ProgramInterface()
    MyProgram.show()
    sys.exit(Program.exec_())
