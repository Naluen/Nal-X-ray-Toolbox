from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import re
import struct

import numpy as np

from module.Module import FileModule

CODE = 'iso-8859-1'

TBL_STEPPING_DRIVERS = {
    0: ("locked coupled", "TWOTHETA"),
    1: ("unlocked coupled", "TWOTHETA"),
    2: ("detector scan", "TWOTHETA"),
    3: ("rocking curve", "OMEGA"),
    4: ("khi scan", "KHI"),
    5: ("phi scan", "PHI"),
    6: ("x-scan", "X"),
    7: ("y-scan", "Y"),
    8: ("z-scan", "Z"),
    9: ("aux1 scan", "AUX1"),
    10: ("aux2 scan", "AUX2"),
    11: ("aux3 scan", "AUX3"),
    12: ("psi scan", "TWOTHETA"),
    13: ("hkl scan", "TWOTHETA"),
    129: ("psd fixed scan", "TWOTHETA"),
    130: ("psd fast scan", "TWOTHETA")
}


class RawFile(FileModule):
    def __init__(self):
        super(RawFile, self).__init__()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return ".raw",

    def get_data(self):
        logging.debug("Transform .raw file data to ndarray...")

        meta_header, scans = self.parser_file()

        attr = meta_header.copy()

        if not scans:
            raise Exception("Empty Dataset.")

        if not all([
                i._STEPPING_DRIVE_CODE == scans[0]._STEPPING_DRIVE_CODE
                for i in scans
        ]):
            raise Exception("Different Scan Type in this file.")

        step_code = scans[0]._STEPPING_DRIVE_CODE

        if step_code in (129, 130):
            # RSM Scan
            attr['STEPS'] = int(scans[0].STEPS)
            attr['STEP_SIZE'] = float(scans[0].STEP_SIZE)
            theta_start = float(scans[0].TWOTHETA)
            if not all(i.PHI == scans[0].PHI for i in scans):
                raise Exception("The Phi is inconsistent.")
            if not all(i.TWOTHETA == scans[0].TWOTHETA for i in scans):
                logging.error("The Two Theta is inconsistent.")
                if 1:
                    scans = [
                        i for i in scans if i.TWOTHETA == scans[0].TWOTHETA
                    ]
            if not all(i.STEP_SIZE == scans[0].STEP_SIZE for i in scans):
                raise Exception("The Step Size is inconsistent.")
            if not all(i.STEPS == scans[0].STEPS for i in scans):
                raise Exception("The Steps is inconsistent.")

            attr['TYPE'] = 'RSMPlot'
            attr['PHI'] = float(scans[0].PHI)
            attr['STEPPING_DRIVE1'] = 'OMEGA'
            attr['OMEGA'] = np.asarray([float(i.OMEGA) for i in scans])
            attr['TWOTHETA'] = np.linspace(
                theta_start, theta_start + attr['STEP_SIZE'] * attr['STEPS'],
                attr['STEPS'])
            for i in scans:
                if len(i.intensity) < len(scans[0].intensity):
                    diff = len(scans[0].intensity) - len(i.intensity)
                    i.intensity = np.pad(
                        np.asarray(i.intensity), (0, diff),
                        'constant',
                        constant_values=(0, 0)).tolist()
            data = (np.asanyarray([i.intensity
                                   for i in scans]) / scans[0].STEP_TIME)
        elif step_code is 13:
            raise Exception("Unknown Scan Type")
        else:
            if len(scans) == 1:
                drv = TBL_STEPPING_DRIVERS[step_code][1]
                attr['STEP_TIME'] = float(scans[0].STEP_TIME)
                attr['STEPPING_DRIVE1'] = drv
                attr['STEP_SIZE'] = float(scans[0].STEP_SIZE)
                attr['TYPE'] = 'SingleScan'

                drv_x = np.linspace(
                    float(scans[0].header[drv]),
                    float(scans[0].header[drv]) +
                    float(scans[0].STEP_SIZE) * int(scans[0].STEPS),
                    int(scans[0].STEPS))
                data = np.vstack(
                    (drv_x,
                     np.asarray(scans[0].intensity) / attr['STEP_TIME']))

                if step_code is 3:
                    attr['TYPE'] = "RockingCurve"
            else:
                if not all(i.STEP_SIZE == scans[0].STEP_SIZE for i in scans):
                    raise Exception("The Step Size is inconsistent.")
                if not all(i.STEPS == scans[0].STEPS for i in scans):
                    raise Exception("The Steps is inconsistent.")
                if not all(i.STEP_TIME == scans[0].STEP_TIME for i in scans):
                    raise Exception("The Step Time is inconsistent.")
                drivers = ['KHI', 'PHI', 'X', 'Y', 'Z', 'AUX1', 'AUX2', 'AUX3']
                for drv in drivers:
                    if scans[0].header[drv] != scans[1].header[drv]:
                        attr['STEPPING_DRIVE1'] = drv
                        attr['STEPPING_DRIVE2'] = \
                        TBL_STEPPING_DRIVERS[step_code][1]
                        break

                drv_2_n = attr['STEPPING_DRIVE2']
                if not all(i.header[drv_2_n] == scans[0].header[drv_2_n]
                           for i in scans):
                    if 1:
                        scans = [
                            i for i in scans
                            if i.header[drv_2_n] == scans[0].header[drv_2_n]
                        ]

                attr['DRV_1'] = np.asarray(
                    [float(i.header[attr['STEPPING_DRIVE1']]) for i in scans])
                attr['DRV_2'] = np.linspace(
                    float(scans[0].header[attr['STEPPING_DRIVE2']]),
                    float(scans[0].header[attr['STEPPING_DRIVE2']]) +
                    float(scans[0].STEP_SIZE) * int(scans[0].STEPS),
                    int(scans[0].STEPS))
                attr['TYPE'] = 'TwoDPlot'
                for i in scans:
                    if len(i.intensity) < len(scans[0].intensity):
                        diff = len(scans[0].intensity) - len(i.intensity)
                        i.intensity = np.pad(
                            np.asarray(i.intensity), (0, diff),
                            'constant',
                            constant_values=(0, 0)).tolist()
                data = (np.asanyarray([i.intensity for i in scans]) / float(
                    scans[0].STEP_TIME))

                if attr['STEPPING_DRIVE1'] == "KHI":
                    if attr['STEPPING_DRIVE2'] == 'PHI':
                        attr['TYPE'] = 'PolesFigurePlot'
                        attr['VIT_ANGLE'] = float(
                            scans[0].STEP_SIZE / scans[0].STEP_TIME)

        return data, attr

    def parser_file(self):
        """Factory method for diffrent version of raw files."""
        with open(self.file, 'rb') as file_handle:
            _version = file_handle.read(4).decode(CODE)
            if _version == "RAW1":
                _version = _version + file_handle.read(3).decode(CODE)
            assert _version in ("RAW ", "RAW2", "RAW1.01")
            if _version == 'RAW':
                return self.load_version1(file_handle)
            elif _version == 'RAW2':
                return self.load_version2(file_handle)
            else:
                return self.load_version3(file_handle)

    @staticmethod
    def load_version1(file_handle):
        """Parser version.RAW ."""
        meta_header = {'FORMAT_VERSION': "v1"}

        return meta_header,

    @staticmethod
    def load_version2(file_handle):
        """Parser version.RAW2."""
        meta_header = {'FORMAT_VERSION': "v2"}

        return meta_header,

    @staticmethod
    def load_version3(file_handle):
        """Parser version.RAW1.01."""
        file_handle.seek(8, os.SEEK_SET)
        meta_header = {}
        meta_header['FORMAT_VERSION'] = "v3"
        meta_header['_FILE_STATUS_CODE'] = struct.unpack(
            'I', file_handle.read(4))[0]
        meta_header['RANGE_CNT'] = struct.unpack('I', file_handle.read(4))[0]
        meta_header['DATE'] = file_handle.read(10).decode(CODE)
        meta_header['TIME'] = file_handle.read(10).decode(CODE)
        meta_header['USER'] = file_handle.read(72).decode(CODE)
        meta_header['SITE'] = file_handle.read(218).decode(CODE)
        meta_header['SAMPLE_ID'] = file_handle.read(60).decode(CODE)
        meta_header['COMMENT'] = file_handle.read(160).decode(CODE)
        file_handle.seek(2, os.SEEK_CUR)  # Error in File Design
        file_handle.seek(4, os.SEEK_CUR)  # goniometer code
        file_handle.seek(4, os.SEEK_CUR)  # goniometer stage code
        file_handle.seek(4, os.SEEK_CUR)  # sample loader code
        file_handle.seek(4, os.SEEK_CUR)  # goniometer controller code
        file_handle.seek(4, os.SEEK_CUR)  # (R4) goniometer radius
        file_handle.seek(4, os.SEEK_CUR)  # (R4) fixed divergence...
        file_handle.seek(4, os.SEEK_CUR)  # (R4) fixed sample slit...
        file_handle.seek(4, os.SEEK_CUR)  # primary Soller slit
        file_handle.seek(4, os.SEEK_CUR)  # primary monochromator
        file_handle.seek(4, os.SEEK_CUR)  # (R4) fixed anti-scatter...
        file_handle.seek(4, os.SEEK_CUR)  # (R4) fixed detector slit...
        file_handle.seek(4, os.SEEK_CUR)  # secondary Soller slit
        file_handle.seek(4, os.SEEK_CUR)  # fixed thin film attachment
        file_handle.seek(4, os.SEEK_CUR)  # beta filter
        file_handle.seek(4, os.SEEK_CUR)  # secondary monochromator
        meta_header["ANODE_MATERIAL"] = file_handle.read(4).decode(CODE)
        file_handle.seek(4, os.SEEK_CUR)  # unused
        meta_header["ALPHA_AVERAGE"] = struct.unpack('d',
                                                     file_handle.read(8))[0]
        meta_header["ALPHA1"] = struct.unpack('d', file_handle.read(8))[0]
        meta_header["ALPHA2"] = struct.unpack('d', file_handle.read(8))[0]
        meta_header["BETA"] = struct.unpack('d', file_handle.read(8))[0]
        meta_header["ALPHA_RATIO"] = struct.unpack('d', file_handle.read(8))[0]
        file_handle.seek(4, os.SEEK_CUR)  # (C4) unit name
        file_handle.seek(4, os.SEEK_CUR)  # (R4) intensity beta: a1
        meta_header["MEASUREMENT TIME"] = struct.unpack(
            'I', file_handle.read(4))[0]
        file_handle.seek(43, os.SEEK_CUR)  # unused
        file_handle.seek(1, os.SEEK_CUR)  # hardware dependency...
        assert file_handle.tell() == 712

        scans = [
            ScanBulk(file_handle) for _ in range(meta_header['RANGE_CNT'])
        ]

        return meta_header, scans


class ScanBulk(object):
    """Record each scan in the raw file."""

    def __init__(self, file_handle):
        header = {}
        header_len = struct.unpack('I', file_handle.read(4))[0]  # address 0
        assert header_len == 304
        header["STEPS"] = struct.unpack('I', file_handle.read(4))[0]
        header["OMEGA"] = struct.unpack('d', file_handle.read(8))[0]
        header["TWOTHETA"] = struct.unpack('d', file_handle.read(8))[0]
        header["KHI"] = struct.unpack('d', file_handle.read(8))[0]
        header["PHI"] = struct.unpack('d', file_handle.read(8))[0]
        header["X"] = struct.unpack('d', file_handle.read(8))[0]
        header["Y"] = struct.unpack('d', file_handle.read(8))[0]
        header["Z"] = struct.unpack('d', file_handle.read(8))[0]
        file_handle.seek(8, os.SEEK_CUR)  # address 64
        file_handle.seek(6, os.SEEK_CUR)  # address 72
        file_handle.seek(2, os.SEEK_CUR)  # address 78
        file_handle.seek(8, os.SEEK_CUR)  # (R8) variable antiscat.
        file_handle.seek(6, os.SEEK_CUR)  # address 88
        # unused                   # address 94
        file_handle.seek(2, os.SEEK_CUR)
        header["DETECTOR"] = struct.unpack('I', file_handle.read(4))[0]
        header["HIGH_VOLTAGE"] = struct.unpack('f', file_handle.read(4))[0]
        header["AMPLIFIER_GAIN"] = struct.unpack('f', file_handle.read(4))[0]
        header["DISCRIMINATOR_1_LOWER_LEVEL"] = struct.unpack(
            'f', file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 112
        file_handle.seek(4, os.SEEK_CUR)  # address 116
        file_handle.seek(8, os.SEEK_CUR)  # address 120
        file_handle.seek(4, os.SEEK_CUR)  # address 128
        file_handle.seek(4, os.SEEK_CUR)  # address 132
        file_handle.seek(5, os.SEEK_CUR)  # address 136
        # unused                   # address 141
        file_handle.seek(3, os.SEEK_CUR)
        header["AU1"] = struct.unpack('d', file_handle.read(8))[0]
        header["AU2"] = struct.unpack('d', file_handle.read(8))[0]
        header["AU3"] = struct.unpack('d', file_handle.read(8))[0]
        header["SCAN_MODE"] = struct.unpack('I', file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 176
        header["STEP_SIZE"] = struct.unpack('d', file_handle.read(8))[0]
        header["STEP_SIZE_B"] = struct.unpack('d', file_handle.read(8))[0]
        header["STEP_TIME"] = struct.unpack('f', file_handle.read(4))[0]
        header["_STEPPING_DRIVE_CODE"] = struct.unpack('I',
                                                       file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 204
        header["ROTATION_SPEED [rpm]"] = struct.unpack('f',
                                                       file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 212
        header["TEMP_RATE"] = struct.unpack('f', file_handle.read(4))[0]
        header["TEMP_DELAY"] = struct.unpack('f', file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)
        header["GENERATOR_VOLTAGE"] = struct.unpack('f',
                                                    file_handle.read(4))[0]
        header["GENERATOR_CURRENT"] = struct.unpack('f',
                                                    file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 232
        # unused                  # address 236
        file_handle.seek(4, os.SEEK_CUR)
        header["USED_LAMBDA"] = struct.unpack('d', file_handle.read(8))[0]
        header['_VARYINGPARAMS'] = struct.unpack('I', file_handle.read(4))[0]
        header['_DATUM_LENGTH'] = struct.unpack('I', file_handle.read(4))[0]
        supplementary_headers_size = struct.unpack('I', file_handle.read(4))[0]
        file_handle.seek(4, os.SEEK_CUR)  # address 260
        file_handle.seek(4, os.SEEK_CUR)  # address 264

        file_handle.seek(4, os.SEEK_CUR)  # address 268
        file_handle.seek(8, os.SEEK_CUR)  # address 272
        file_handle.seek(24, os.SEEK_CUR)  # address 280
        if supplementary_headers_size:
            file_handle.seek(supplementary_headers_size, os.SEEK_CUR)
        self.intensity = struct.unpack(
            str(header["STEPS"]) + "f", file_handle.read(4 * header["STEPS"]))
        self.header = header
        for k, value in header.items():
            setattr(self, k, value)


if __name__ == '__main__':
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    RAW_FILE = RawFile()
    RAW_FILE.get_file(os.path.join("..", "test", "test_data", "002.raw"))
    META, SCANS = RAW_FILE.parser_file()
