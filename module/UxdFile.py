import re

import numpy as np

from module.Module import FileModule

TBL_STEPPING_DRIVERS = {
    "'PSDFIXED'": "TWOTHETA"
}

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
        from itertools import groupby, filterfalse

        data_list = [
            list(g) for k, g in groupby(data_list, lambda x: x.startswith(";"))
        ]
        data_list = list(
            filterfalse(lambda x: x[0].startswith(";"), data_list)
        )

        header = {
            i.split('=')[0].strip(): i.split('=')[1].strip()
            for i in data_list[0] if i.startswith("_")
        }
        attr = {}
        if "_TYPE" in header:
            data_list = data_list[1:]
        else:
            data_list = data_list[4:]

            for k in data_list[0]:
                if k.startswith("_DRIVE"):
                    driver = k.split('=')[1]
            if re.search("psd", driver.lower()):
                header['_TYPE'] = 'RSMPlot'
                header['_STEPPING_DRIVE1'] = 'OMEGA'
                header['_STEPPING_DRIVE2'] = TBL_STEPPING_DRIVERS[driver]

        if header['_TYPE'] == 'TwoDPlot':
            attr['DRV_1'] = self.one_d_data(
                    data_list, '_%s' % header['_STEPPING_DRIVE1'])[0]
            attr['DRV_2'] = self.two_d_data(data_list, 0)[0, :]

            step_time = self.one_d_data(data_list, '_STEPTIME')[0]

            data = self.two_d_data(data_list, 1) / step_time

            # Delete empty scans.
            w, _ = data.shape
            attr['DRV_1'] = attr['DRV_1'][:w]

            if header['_STEPPING_DRIVE1'] == 'KHI':
                if header['_STEPPING_DRIVE2'] == 'PHI':
                    phi_data = self.two_d_data(data_list, 0)
                    attr['VIT_ANGLE'] = (
                            (phi_data[0, 1] - phi_data[0, 0]) / step_time)
                    attr['TYPE'] = 'PolesFigurePlot'

        elif header['_TYPE'] == 'RSMPlot':
            attr['TYPE'] = "RSMPlot"
            attr['PHI'] = float(self.one_d_data(data_list, '_PHI')[0])

            attr['OMEGA'] = self.one_d_data(data_list, '_OMEGA')

            attr['TWOTHETA'] = self.two_d_data(data_list, 0)[0]

            step_time = self.one_d_data(data_list, '_STEPTIME')[0]

            data = self.two_d_data(data_list, 1) / step_time

            # Delete empty scans.
            w, _ = data.shape
            attr['OMEGA'] = attr['OMEGA'][:w]

            # For some version of uxd file.
            if not attr['OMEGA'][0]:
                start = self.one_d_data(data_list, '_START')[0]
                step = self.one_d_data(data_list, '_STEPSIZE')[0]
                attr['OMEGA'] = np.linspace(start, start+step*w, w)

        elif header['_TYPE'] == 'SingleScanPlot':
            step_time = self.one_d_data(data_list, '_STEPTIME')[0]
            data = np.vstack((self.two_d_data(data_list, 0),
                              self.two_d_data(data_list, 1)/step_time))
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

        attr['STEP_TIME'] = float(self.one_d_data(data_list, '_STEPTIME')[0])
        attr['STPES'] = int(self.one_d_data(data_list, '_STEPS')[0])
        attr['STEP_SIZE'] = float(self.one_d_data(data_list, '_STEP_SIZE')[0])

        return data, attr

    @staticmethod
    def two_d_data(data_list, index):
        try:
            data = [[
                float(j.split('\t')[index]) for j in value
                if (re.match('\d', j) or j.startswith("-"))
            ] for value in data_list]
        except (ValueError, IndexError):
            data = [
                [float(j.split()[index]) for j in value
                 if (re.match('\d', j) or j.startswith("-"))]
                for value in data_list]
        data = [i for i in data if i]
        data = np.asanyarray(data)
        return data

    @staticmethod
    def one_d_data(data_list, key_word):
        # one_d_data([["A=0"], ["B=3"], ["A=1"]], "A") -> array([0, 1])
        data = [
            [float(j.split('=')[1]) for j in value if j.startswith(key_word)]
            for value in data_list]
        data = np.asarray([i[0] if len(i) > 0 else 0 for i in data])
        return data


if __name__ == '__main__':
    import os

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    f = UxdFile()
    f.get_file(os.path.join("..", "test", "test_data", "002_01.UXD"))
    f.get_data()
