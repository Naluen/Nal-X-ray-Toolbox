import logging

import numpy

from module.Module import FileModule


class H5File(FileModule):
    """The module to support H5File.

    """
    import h5py

    def __init__(self):
        self.fh = None

    @property
    def name(self):
        return "H5File"

    @property
    def supp_type(self):
        return ".h5"

    def get_file(self, h5_file):
        self.fh = self.h5py.File(h5_file, 'a')

    def file2narray(self):
        pass

    def set_data(self, data, path, name, attr, is_force=None):
        """

        :param data:
        :param path:
        :param name:
        :param attr:
        :param is_force: True will overwrite existed data set.
        :return:
        """
        if isinstance(data, numpy.ndarray):
            logging.debug("This is a numpy array instant.")
            if isinstance(self.fh[path], self.h5py.Dataset):
                grp = self.fh[path].parent
            elif isinstance(self.fh[path], self.h5py.Group):
                grp = self.fh[path]
            else:
                raise FileNotFoundError

            if name in grp and isinstance(grp[name], self.h5py.Dataset):
                if is_force:
                    del grp[name]
                else:
                    raise FileExistsError

            dt = grp.create_dataset(
                name,
                data=data,
                chunks=True,
                compression="gzip",
            )
            print(dt)

            for i in attr.keys():
                logging.debug("Writing {0}: {1}".format(i, attr[i]))

                try:
                    if isinstance(attr[i], numpy.ndarray):
                        dt.attrs.create(i, data=attr[i])
                    else:
                        dt.attrs[i] = attr[i]
                except TypeError:
                    logging.debug("Fail to write {0}: {1}".format(i, attr[i]))

        else:
            raise TypeError(
                "Unknown input data type."
                "Only ndarray could be written into h5file")


            # def get_recipe_plot(self):
            #     """
            #     Plot recipe in current axis.
            #     :return: None
            #     """
            #     from matplotlib.patches import Rectangle
            #
            #     self.get_recipe()
            #     mat_dict = {0: Si(),
            #                 1: GaP(),
            #                 2: AlGaP(),
            #                 3: GaPN()}
            #
            #     ax = plt.gca()
            #
            #     ax.spines["top"].set_visible(False)
            #     ax.spines["bottom"].set_visible(False)
            #     ax.spines["right"].set_visible(False)
            #     ax.spines["left"].set_visible(False)
            #
            #     ax.tick_params(
            #         axis="both", which="both", bottom="off", top="off",
            #         labelbottom="off",
            #         left="off", right="off", labelleft="off")
            #
            #     ax.set_aspect('auto')
            #
            #     tk = 0
            #     for i in self.__recipe:
            #         if 1 < i[3] <= 100:
            #             height = i[3] / 10
            #         elif 100 < i[3] <= 1000:
            #             height = i[3] / 40
            #         elif i[3] > 1000:
            #             height = i[3] / 100
            #         # elif i[3] > 2000:
            #         #     height = i[3] / 500
            #         elif i[3] == 0:
            #             height = 10
            #         else:
            #             height = i[3]
            #         ax.add_patch(
            #             Rectangle((0.2, tk), width=2, height=height,
            #                       color=mat_dict[i[0]].color,
            #                       label=mat_dict[i[0]].form_name)
            #         )
            #         tk += height
            #
            #     ax.set_xlim(0, 2.5)
            #     ax.set_ylim(0, tk * 1.05)
            #
            #     from collections import OrderedDict
            #     handles, labels = plt.gca().get_legend_handles_labels()
            #     by_label = OrderedDict(zip(labels, handles))
            #     plt.legend(by_label.values(), by_label.keys(), loc='best')

            # def create_scan_instance(self):
            #     scan_type = str(self.get_scan_type())
            #     try:
            #         scan_instance = SCAN_TYPE_DICT[scan_type]()
            #     except KeyError:
            #         logging.debug("Scan Type is {0}".format(scan_type))
            #     else:
            #         return scan_instance
            #
            # def get_scan_dict(self):
            #     scan_dict = {i: self.file_handle.attrs[i]
            #                  for i in self.file_handle.attrs.keys()}
            #
            #     if 'sample' not in scan_dict:
            #         scan_dict['sample'] = self.file[1].split(r'/')[0]
            #
            #     return scan_dict
            #
            # def get_scan_type(self):
            #     scan_type = self.file_handle.attrs.get('_TYPE')
            #
            #     return scan_type
            #
            # def set_scan_dict(self, scan_dict):
            #     for i in self.file_handle.attrs.keys():
            #         del self.file_handle.attrs[i]
            #     for i in scan_dict:
            #         self.file_handle.attrs[i] = scan_dict[i]
            #
            # def read_data(self):
            #     scan_instance = self.create_scan_instance()
            #     data_set = self.file_handle.items()
            #
            #     scan_instance.set_data_dict({i[0]: np.asarray(i[1]) for i in data_set})
            #     scan_instance.set_scan_dict(self.get_scan_dict())
            #
            #     logging.debug("Scan dict: {0}".format(self.get_scan_dict()))
            #
            #     return scan_instance
            #
            # def set_rcp(self, rcp):
            #     """
            #     Save recipe in current branch.
            #     :return:
            #     """
            #     if 'Recipe' in self.file_handle:
            #         del self.file_handle['Recipe']
            #     self.file_handle.create_group('Recipe')
            #     self.file_handle['Recipe'].create_dataset('Recipe', data=rcp)
            #     self.file_handle['Recipe'].attrs['_TYPE'] = 'Recipe'
            #
            # def get_rcp(self):
            #     if 'Recipe' in self.file_handle:
            #         return self.file_handle['Recipe/Recipe']
            #     else:
            #         return None
            #
            # recipe = property(get_rcp, set_rcp)

    def is_data_set(self, path):
        if isinstance(self.fh[path], self.h5py.Dataset):
            return 0
        elif isinstance(self.fh[path], self.h5py.Group):
            return 1
        else:
            return 2
