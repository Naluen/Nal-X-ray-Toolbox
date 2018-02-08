import re

import numpy as np

from module.Module import FileModule


class UxdFile(FileModule):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return 'UxdFile'

    @property
    def supp_type(self):
        return ".uxd",

    def get_data(self):
        with open(self.file, 'r') as file_handle:
            data_list = [line.strip() for line in file_handle]

        new_data_list = []
        cube = []
        for i in data_list:
            if i.startswith('; (Data for Range number'):
                new_data_list.append(cube)
                cube = []
            else:
                cube.append(i)
        data_list = new_data_list

        header = {
            i.split('=')[0].strip(): i.split('=')[1].strip()
            for i in data_list[0] if i.startswith("_")
        }
        attr = {}

        if header['_TYPE'] == 'TwoDPlot':
            attr['DRV_1'] = \
                self.one_d_data(
                    data_list, '_%s' % header['_STEPPING_DRIVE1'])[0]
            attr['DRV_2'] = self.two_d_data(data_list, 0)[0, :]

            data = self.two_d_data(data_list, 1)

            w, _ = data.shape
            attr['DRV_1'] = attr['DRV_1'][:w]

            if header['_STEPPING_DRIVE1'] == 'KHI':
                if header['_STEPPING_DRIVE2'] == 'PHI':
                    phi_data = self.two_d_data(data_list, 0)
                    attr['VIT_ANGLE'] = ((
                        phi_data[0, 1] - phi_data[0, 0]) / self.one_d_data(
                            data_list, '_STEPTIME')[0][0])
                    attr['TYPE'] = 'PolesFigurePlot'

        elif header['_TYPE'] == 'RSMPlot':
            attr['TYPE'] = "RSMPlot"
            attr['PHI'] = float(self.one_d_data(data_list, '_PHI')[0])
            attr['OMEGA'] = self.one_d_data(data_list, '_OMEGA')
            attr['TWOTHETA'] = self.two_d_data(data_list, 0)[0]

            data = self.two_d_data(data_list, 1)

            w, _ = data.shape
            attr['OMEGA'] = attr['OMEGA'][:w]

        elif header['_TYPE'] == 'SingleScanPlot':
            data = np.vstack((self.two_d_data(data_list, 0),
                              self.two_d_data(data_list, 1)))
            attr['TYPE'] = 'SingleScan'
            try:
                if header['_SCAN_TYPE'] == 'rocking curve':
                    attr['TYPE'] = "RockingCurve"
            except KeyError:
                pass
        else:
            return

        attr['STEPPING_DRIVE2'] = header['_STEPPING_DRIVE2']
        attr['STEPPING_DRIVE1'] = header['_STEPPING_DRIVE1']

        attr['STEP_TIME'] = float(
            self.one_d_data(data_list, '_STEPTIME')[0][0])
        attr['STPES'] = int(self.one_d_data(data_list, '_STEPS')[0][0])
        attr['STEP_SIZE'] = float(
            self.one_d_data(data_list, '_STEP_SIZE')[0][0])

        return data, attr

    @staticmethod
    def two_d_data(data_list, index):
        data = [[
            float(j.split('\t')[index]) for j in value
            if (re.match('\d', j) or j.startswith("-"))
        ] for value in data_list[1:]]
        data = [i for i in data if i]
        data = np.asanyarray(data)
        return data

    @staticmethod
    def one_d_data(data_list, key_word):
        data = np.asarray(
            [[float(j.split('=')[1]) for j in value if j.startswith(key_word)]
             for value in data_list[1:]])
        return data


if __name__ == '__main__':
    import os

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    f = UxdFile()
    f.get_file(os.path.join("..", "test", "test_data", "002.uxd"))
    f.get_data()
