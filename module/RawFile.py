from __future__ import print_function
from __future__ import unicode_literals

import collections
import copy
import io
import logging
import os
import re
import struct

import numpy as np

from module.Module import FileModule

CODE = 'iso-8859-1'


class RawFile(FileModule):
    def __init__(self):
        super(RawFile, self).__init__()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return ".raw",

    @staticmethod
    def two_d_data(data_list, index):
        data = [
            [float(j.split('\t')[index]) for j in
             value
             if (re.match('\d', j) or j.startswith("-"))]
            for value in data_list[1:]
        ]
        i_1 = data[0]
        for i in range(len(data)):
            if len(data[i]) < len(i_1):
                data[i] = i_1

        return np.asanyarray(data)

    @staticmethod
    def one_d_data(data_list, key_word):
        data = np.asarray(
            [
                [float(j.split('=')[1]) for j
                 in value if j.startswith(key_word)]
                for value in data_list[1:]
            ]
        )
        return data

    def file2narray(self):
        logging.debug("Transform .raw file data to ndarray...")

        with open(self.file, 'rb') as fp:
            ds = DatasetDiffractPlusV3(fp)
        data_string = ds.pretty_format(print_header=True)
        data_list = data_string.split('\n')
        from itertools import groupby
        data_list = [list(g) for k, g in
                     groupby((line.strip() for line in data_list), bool) if k]

        attr = {i.split('=')[0].strip(): i.split('=')[1].strip()
                for i in data_list[0] if i.startswith("_")}
        logging.debug("Raw file attr is: {0}".format(attr))

        if attr['_TYPE'] == 'TwoDPlot':
            if (
                    (attr['_STEPPING_DRIVE1'] == 'KHI') and
                    (attr['_STEPPING_DRIVE2'] == 'PHI')):
                khi_data = self.one_d_data(data_list, '_KHI')
                attr['khi_min'] = np.int16(khi_data[0][0])
                attr['khi_max'] = np.int16(khi_data[-1][0])
                phi_data = self.two_d_data(data_list, 0)
                attr['phi_min'] = np.int16(phi_data[0, :][0])
                attr['phi_max'] = np.int16(phi_data[0, :][-1])

                data = self.two_d_data(data_list, 1)
                size = self.one_d_data(data_list, '_STEP_SIZE')[0][0]
                tm = self.one_d_data(data_list, '_STEPTIME')[0][0]
                attr['vit_ang'] = np.float32(size / tm)
                attr['Type'] = "PolesFigure"

        elif attr['_TYPE'] == 'RSMPlot':
            if (
                    (attr['_STEPPING_DRIVE1'] == 'OMEGA') and
                    (attr['_STEPPING_DRIVE2'] == 'TWOTHETA')):
                attr['Type'] = "RSM"
                attr['phi_data'] = self.one_d_data(data_list, '_PHI')
                attr['omega_data'] = self.one_d_data(data_list, '_OMEGA')
                attr['two_theta_data'] = self.two_d_data(data_list, 0)[0]

                data = self.two_d_data(data_list, 1)

        elif attr['_TYPE'] == 'SingleScanPlot':
            attr['_STEP_SIZE'] = self.one_d_data(data_list, '_STEP_SIZE')[0][0]
            attr['_STEPTIME'] = self.one_d_data(data_list, '_STEPTIME')[0][0]
            data = np.vstack(
                (
                    self.two_d_data(data_list, 0),
                    self.two_d_data(data_list, 1) / attr['_STEPTIME']
                )
            )
            if attr['_SCAN_TYPE'] == 'detector scan':
                attr['Type'] = "SingleScan"
            elif attr['_SCAN_TYPE'] == 'rocking curve':
                attr['Type'] = "RockingCurve"

        return data, attr

    def parser_file(self):
        with open(self.file, 'rb') as fp:
            _version = fp.read(4).decode(CODE)
            if _version == "RAW1":
                _version = _version + fp.read(3).decode(CODE)
            assert _version in ("RAW ", "RAW2", "RAW1.01")
            if _version == 'RAW':
                self.load_version1(fp)
            elif _version == 'RAW2':
                self.load_version2(fp)
            else:
                self.load_version3(fp)

    @staticmethod
    def load_version1(fh):
        meta_header = {'FORMAT VERSION': "v1"}

        return meta_header,

    @staticmethod
    def load_version2(fh):
        meta_header = {'FORMAT VERSION': "v2"}

        return meta_header,

    @staticmethod
    def load_version3(fh):
        fh.seek(8, os.SEEK_SET)
        meta_header = {}
        meta_header['FORMAT VERSION'] = "v3"
        meta_header['_FILE_STATUS_CODE'] = struct.unpack('I', fh.read(4))[0]
        meta_header['RANGE_CNT'] = struct.unpack('I', fh.read(4))[0]
        meta_header['DATE'] = fh.read(10).decode(CODE)
        meta_header['TIME'] = fh.read(10).decode(CODE)
        meta_header['USER'] = fh.read(72).decode(CODE)
        meta_header['SITE'] = fh.read(218).decode(CODE)
        meta_header['SAMPLE_ID'] = fh.read(60).decode(CODE)
        meta_header['COMMENT'] = fh.read(160).decode(CODE)
        fh.seek(2, os.SEEK_CUR)  # Error in File Design
        fh.seek(4, os.SEEK_CUR)  # goniometer code 
        fh.seek(4, os.SEEK_CUR)  # goniometer stage code 
        fh.seek(4, os.SEEK_CUR)  # sample loader code
        fh.seek(4, os.SEEK_CUR)  # goniometer controller code
        fh.seek(4, os.SEEK_CUR)  # (R4) goniometer radius
        fh.seek(4, os.SEEK_CUR)  # (R4) fixed divergence...
        fh.seek(4, os.SEEK_CUR)  # (R4) fixed sample slit...
        fh.seek(4, os.SEEK_CUR)  # primary Soller slit
        fh.seek(4, os.SEEK_CUR)  # primary monochromator
        fh.seek(4, os.SEEK_CUR)  # (R4) fixed anti-scatter...
        fh.seek(4, os.SEEK_CUR)  # (R4) fixed detector slit...
        fh.seek(4, os.SEEK_CUR)  # secondary Soller slit
        fh.seek(4, os.SEEK_CUR)  # fixed thin film attachment
        fh.seek(4, os.SEEK_CUR)  # beta filter
        fh.seek(4, os.SEEK_CUR)  # secondary monochromator
        meta_header["ANODE_MATERIAL"] = fh.read(4).decode(CODE)
        fh.seek(4, os.SEEK_CUR)  # unused
        meta_header["ALPHA_AVERAGE"] = struct.unpack('d', fh.read(8))[0]
        meta_header["ALPHA1"] = struct.unpack('d', fh.read(8))[0]
        meta_header["ALPHA2"] = struct.unpack('d', fh.read(8))[0]
        meta_header["BETA"] = struct.unpack('d', fh.read(8))[0]
        meta_header["ALPHA_RATIO"] = struct.unpack('d', fh.read(8))[0]
        fh.seek(4, os.SEEK_CUR)  # (C4) unit name
        fh.seek(4, os.SEEK_CUR)  # (R4) intensity beta: a1
        meta_header["MEASUREMENT TIME"] = struct.unpack('I', fh.read(4))[0]
        fh.seek(43, os.SEEK_CUR)  # unused
        fh.seek(1, os.SEEK_CUR)  # hardware dependency...
        assert (fh.tell() == 712)

        logging.debug("=" * 36)
        logging.debug("Meta Header has been read.")
        logging.debug(
            os.linesep + "".join(
                ["{0}: {1} {2}".format(i, meta_header[i], os.linesep)
                 for i in meta_header.keys()]
            )
        )
        logging.debug("=" * 36)

        for i in range(meta_header['RANGE_CNT']):
            header = {}
            header_len = struct.unpack('I', fh.read(4))[0]  # address 0
            assert (header_len == 304)
            header["STEPS"] = struct.unpack('I', fh.read(4))[0]
            header["OMEGA"] = struct.unpack('d', fh.read(8))[0]
            header["2THETA"] = struct.unpack('d', fh.read(8))[0]
            header["KHI"] = struct.unpack('d', fh.read(8))[0]
            header["PHI"] = struct.unpack('d', fh.read(8))[0]
            header["X"] = struct.unpack('d', fh.read(8))[0]
            header["Y"] = struct.unpack('d', fh.read(8))[0]
            header["Z"] = struct.unpack('d', fh.read(8))[0]
            fh.seek(8, os.SEEK_CUR)  # address 64
            fh.seek(6, os.SEEK_CUR)  # address 72
            fh.seek(2, os.SEEK_CUR)  # unused                   # address 78
            fh.seek(8, os.SEEK_CUR)  # (R8) variable antiscat.  # address 80
            fh.seek(6, os.SEEK_CUR)  # address 88
            fh.seek(2, os.SEEK_CUR)  # unused                   # address 94
            header["DETECTOR"] = struct.unpack('I', fh.read(4))[0]
            header["HIGH_VOLTAGE"] = struct.unpack('f', fh.read(4))[0]
            header["AMPLIFIER_GAIN"] = struct.unpack('f', fh.read(4))[0]
            header["DISCRIMINATOR_1_LOWER_LEVEL"] = struct.unpack('f', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 112
            fh.seek(4, os.SEEK_CUR)  # address 116
            fh.seek(8, os.SEEK_CUR)  # address 120
            fh.seek(4, os.SEEK_CUR)  # address 128
            fh.seek(4, os.SEEK_CUR)  # address 132
            fh.seek(5, os.SEEK_CUR)  # address 136
            fh.seek(3, os.SEEK_CUR)  # unused                   # address 141
            header["AU1"] = struct.unpack('d', fh.read(8))[0]
            header["AU2"] = struct.unpack('d', fh.read(8))[0]
            header["AU3"] = struct.unpack('d', fh.read(8))[0]
            header["SCAN_MODE"] = struct.unpack('I', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 176
            header["STEP_SIZE"] = struct.unpack('d', fh.read(8))[0]
            header["STEP_SIZE_B"] = struct.unpack('d', fh.read(8))[0]
            header["STEP_TIME"] = struct.unpack('f', fh.read(4))[0]
            header["_STEPPING_DRIVE_CODE"] = struct.unpack('I', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 204
            header["ROTATION_SPEED [rpm]"] = struct.unpack('f', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 212
            header["TEMP_RATE"] = struct.unpack('f', fh.read(4))[0]
            header["TEMP_DELAY"] = struct.unpack('f', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)
            header["GENERATOR_VOLTAGE"] = struct.unpack('f', fh.read(4))[0]
            header["GENERATOR_CURRENT"] = struct.unpack('f', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 232
            fh.seek(4, os.SEEK_CUR)  # unused                  # address 236
            header["USED_LAMBDA"] = struct.unpack('d', fh.read(8))[0]
            header['_VARYINGPARAMS'] = struct.unpack('I', fh.read(4))[0]
            header['_DATUM_LENGTH'] = struct.unpack('I', fh.read(4))[0]
            supplementary_headers_size = struct.unpack('I', fh.read(4))[0]
            fh.seek(4, os.SEEK_CUR)  # address 260
            fh.seek(4, os.SEEK_CUR)  # address 264
            fh.seek(4, os.SEEK_CUR)  # unused                 # address 268
            fh.seek(8, os.SEEK_CUR)  # address 272
            fh.seek(24, os.SEEK_CUR)  # unused                 # address 280
            if supplementary_headers_size:
                fh.seek(supplementary_headers_size, os.SEEK_CUR)
            intensity = struct.unpack(
                str(header["STEPS"])+"f", fh.read(4*header["STEPS"])
            )

        return meta_header,


class Metadata(object):
    def __init__(self):
        # use OrderedDictionary if possible ( python > 2.7 )
        if hasattr(collections, 'OrderedDict'):
            self._metadata = collections.OrderedDict()
        else:
            self._metadata = {}

    def __getitem__(self, key):
        return self._metadata[key]

    def __setitem__(self, key, val):
        self._metadata[key] = val

    def __delitem__(self, key):
        del self._metadata[key]

    def __getattr__(self, key):
        if key in self._metadata:
            return self._metadata[key]
        else:
            raise AttributeError('Key\'%s\' does not exists' % key)


class Scan(Metadata):
    def __init__(self):
        Metadata.__init__(self)

        self.data = []  # array.array('f')          # holding scan data

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return "<Scan object containing {0:d} data point(s) at {1:d}".format(
            len(self), id(self))

    def __str__(self):
        return self.pretty_format()

    def pretty_format(self, print_header=True):
        import io
        out = io.StringIO()
        # meta data
        if print_header:
            for k, v in list(self._metadata.items()):
                if float == type(v):
                    print("_{0:<15} = {1:.6f}".format(k, v), file=out)
                else:
                    print("_{0:<15} = {1}".format(k, v), file=out)

        # print scan data
        if self.data:
            for (x, y) in self.data:
                print("{0:.6f}\t{1:.6f}".format(x, y), file=out)
        return out.getvalue()


class Dataset(Metadata):
    """base dataset class defines contents and access specifications.

    parsing functions should be in derived class"""

    def __init__(self):
        Metadata.__init__(self)
        self.scans = []

    # len(ds) : return number of scans
    def __len__(self):
        return len(self.scans)

    def __str__(self):
        return self.pretty_format()

    def __repr__(self):
        if 0 == len(self):
            return '<Empty dataset at 0x{1:x}>'
        else:
            return '<Dataset containing {0:d} scan(s) at 0x{1:x}>'.format(
                len(self), id(self))

    def pretty_format(self, print_header=True):
        """Print dataset's header(optional) and each scan.

        :param print_header:
        :return:
        """
        import io
        out = io.StringIO()

        # print dataset header if told so
        if print_header:
            for k, v in list(self._metadata.items()):
                if float == type(v):
                    print("_{0} = {1:.6f}".format(k, v),
                          file=out)  # 6 decimal for float
                else:
                    try:
                        print(r"_{0} = {1}".format(k, str(v).decode(
                            'ISO-8859-1')), file=out)
                    except AttributeError:
                        print(r"_{0} = {1}".format(k, str(v)), file=out)

        for i in range(len(self.scans)):
            if print_header:
                out.write("\n  ( Data for Range number {0:d} )\n".format(i))
            out.write(self.scans[i].pretty_format(print_header) + "\n")
            pass

        return out.getvalue()

    # check whether selected dataset handler can parse given

    def validate(self, f=None):
        return False

    def parse(self, fh):
        pass

    def merge(self, foreign):
        c = copy.deepcopy(self)
        c.scans.extend(foreign.scans)
        return c


class DatasetDiffractPlusV3(Dataset):
    FILE_HEADER_LENGTH = 712

    #
    # file_header_desc_tbl file header is the first 712 bytes of the
    # file it contains information common to all the following scan
    # 'ranges' it is followed by the header of the first scan range
    #
    # name - name used in meta data dictionary
    # type - code for understood by 'unpack'
    # start -
    # len  - should correspond to the type declared
    #
    file_header_desc_tbl = [
        # ( name                  , type,   start, len )
        ('_FILE_STATUS_CODE', 'I', 8, 4),
        # le tiret signifie qu'il va etre supprime/remplace
        ('RANGE_CNT', 'I', 12, 4),
        ('DATE', 'str', 16, 10),
        ('TIME', 'str', 26, 10),
        ('USER', 'str', 36, 72),
        ('SAMPLE', 'str', 326, 60),
        ('+SAMPLE', 'str', 386, 160),
        ('GNONIOMETER_RADIUS', 'f', 564, 4),
        ('ANODE_MATERIAL', 'str', 608, 4),
        ('WL1', 'd', 624, 8),
        ('WL2', 'd', 632, 8),
        ('WL_UNIT', 'str', 656, 4),
        ('MEASUREMENT TIME', 'f', 664, 4)
    ]  # end of file_header_desc_tbl

    #
    # _header_desc_tbl
    #
    # range header is the first few bytes of each range block   this
    # length is variable and its length is given in the first byte
    #
    # todo : how to tell what the scan type is ?, e.g. omg-2th, omg,
    # etc
    #
    range_header_desc_tbl = [
        # (name , type , length )
        ('HEADER_LENGTH', 'I', 0, 4),  # 0 , 304
        ('STEPS', 'I', 4, 4),  # 4
        ('OMEGA', 'd', 8, 8),  # 8
        ('TWOTHETA', 'd', 16, 8),  # 16
        ('KHI', 'd', 24, 8),  # 24
        ('PHI', 'd', 32, 8),  # 32
        ('X', 'd', 40, 8),  # 40
        ('Y', 'd', 48, 8),  # 48
        ('Z', 'd', 56, 8),  # 56
        ('DETECTOR', 'I', 96, 4),  # 96 0x60
        ('HIGH_VOLTAGE', 'f', 100, 4),  # 100
        ('AMPLIFIER_GAIN', 'f', 104, 4),  # 10
        ('AUX1', 'd', 144, 8),  # 144
        ('AUX2', 'd', 152, 8),  # 144
        ('AUX3', 'd', 160, 8),  # 144
        ('SCAN_MODE', 'I', 168, 4),  # 176
        ('STEP_SIZE', 'd', 176, 8),  # 176
        ('STEP_SIZE_B', 'd', 184, 8),  # 176
        ('STEPTIME', 'f', 192, 4),  # 192
        ('_STEPPING_DRIVE_CODE', 'I', 196, 4),
        ('TIMESTARTED', 'f', 204, 4),  # 204
        ('TEMP_RATE', 'f', 212, 4),  # 212
        ('TEMP_DELAY', 'f', 216, 4),  # 216
        ('KV', 'I', 224, 4),  # 224
        ('MA', 'I', 228, 4),  # 228
        ('RANGE_WL', 'd', 240, 8),  # 240
        ('_VARYINGPARAMS', 'I', 248, 4),
        ('_DATUM_LENGTH', 'I', 252, 4),
        ('SUPPLEMENT_HEADER_SIZE', 'I', 256, 4)  # 256
    ]  # end of range_header_desc_tbl

    tbl_stepping_drives = {
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
        130: ("psd fast scan" "TWOTHETA")
    }

    def __init__(self, ifh=None):
        Dataset.__init__(self)
        self.scans = []  # a list of scans
        if ifh:
            ifh.seek(0, 0)
            self.parse(ifh)
            self.determine_dataset_type()

    #
    # only bruker raw file V3 is served
    #
    def validate(self, fh):
        pos = fh.tell()  # remember where it was
        fh.seek(0, os.SEEK_SET)
        is_rawfile = ("RAW1." == fh.read(5))
        is_v3 = ("01" == fh.read(2))
        fh.seek(pos, os.SEEK_SET)  # just being nice
        return is_rawfile and is_v3

    # Determine dataset_type and set stepping_drive1,2
    def determine_dataset_type(self):

        if len(self.scans) < 1:
            raise Exception("Empty Dataset")

        if len(self.scans) == 1:
            self['TYPE'] = 'SingleScanPlot'
            t = self.scans[0]['_STEPPING_DRIVE_CODE']
            self['SCAN_TYPE'], self['STEPPING_DRIVE1'] = \
                self.tbl_stepping_drives[t]
            return

        a = self.scans[0]
        b = self.scans[1]

        if not a['TYPE'] == b['TYPE']:
            raise Exception(" Donno how to deal with this kinds of scan ")

        if a['_STEPPING_DRIVE_CODE'] in [13]:
            raise Exception(" Donno how to deal with this kinds of scan ")

        # PSD scans
        if a['_STEPPING_DRIVE_CODE'] in [129, 130]:
            self['TYPE'] = 'RSMPlot'
            self['STEPPING_DRIVE1'] = 'OMEGA'
            self['STEPPING_DRIVE2'] = 'TWOTHETA'
            return

        # NOTE :
        # it is assumed that only one axis move during each range
        # so that it is safe to say for 2d scan
        self['TYPE'] = 'TwoDPlot'
        for drv in ['KHI', 'PHI', 'X', 'Y', 'Z', 'AUX1', 'AUX2', 'AUX3']:
            if a[drv] != b[drv]:
                self['STEPPING_DRIVE1'] = drv
                self['STEPPING_DRIVE2'] = a['STEPPING_DRIVE']

        pass

    def parse(self, ifh):
        # read into seekable buffer
        f = io.BytesIO(ifh.read())
        f.seek(0, os.SEEK_SET)

        # valid file type signature
        # if not self.validate(f):
        # raise Exception("The file format is not of 'diffract plus raw file version 3'.")
        # (key,type,start,len) in list_table
        for (k, t, s, l) in self.file_header_desc_tbl:
            f.seek(s, os.SEEK_SET)
            buf = f.read(l)
            if 'str' == t:
                self[k] = buf.rstrip(b'\0')
            elif 'c' == t:
                # TODO rather ackward
                self[k] = ord(struct.unpack(t, buf)[0])
            else:
                self[k] = struct.unpack(t, buf)[0]

        if 1 == self['_FILE_STATUS_CODE']:
            self['FILE_STATUS'] = "done"
        elif 2 == self['_FILE_STATUS_CODE']:
            self['FILE_STATUS'] = "active"
        elif 3 == self['_FILE_STATUS_CODE']:
            self['FILE_STATUS'] = "aborted"
        elif 4 == self['_FILE_STATUS_CODE']:
            self['FILE_STATUS'] = "interrupted"

        # beginning of first range
        f.seek(self.FILE_HEADER_LENGTH, os.SEEK_SET)

        range_start = self.FILE_HEADER_LENGTH  # start of first range
        for i in range(self['RANGE_CNT']):
            scn = Scan()
            scn['SEQ'] = i

            # read range headers
            for (k, t, s, l) in self.range_header_desc_tbl:
                f.seek(s + range_start, os.SEEK_SET)
                buf = f.read(l)
                if 'str' == t:
                    scn[k] = buf.rstrip('\0')
                elif 'c' == t:
                    scn[k] = ord(struct.unpack(t, buf)[0])
                else:
                    scn[k] = struct.unpack(t, buf)[0]

            # some constraint described in file-exchange help file
            assert scn[
                       '_VARYINGPARAMS'] == 0, "non-conforming file format: more than 1 varying parameters in one range "
            assert scn[
                       '_DATUM_LENGTH'] == 4, "non-conforming file format : datum length more than 4 byte "
            assert scn['_STEPPING_DRIVE_CODE'] not in [9, 10,
                                                       11], "non-conforming file format, using AUX* drives"

            # seek to the start of header
            f.seek(range_start + scn['HEADER_LENGTH'], os.SEEK_SET)
            # skip supplement header if exists
            if scn['SUPPLEMENT_HEADER_SIZE'] > 0:
                f.read(scn['SUPPLEMENT_HEADER_SIZE'])

            scn['TYPE'] = \
                self.tbl_stepping_drives[scn['_STEPPING_DRIVE_CODE']][0]
            scn['STEPPING_DRIVE'] = \
                self.tbl_stepping_drives[scn['_STEPPING_DRIVE_CODE']][1]
            x = scn[scn['STEPPING_DRIVE']]
            xstep = scn['STEP_SIZE']

            for i in range(scn['STEPS']):
                y = struct.unpack('f', f.read(4))[0]
                scn.data.append((x, y))
                x = x + xstep

            self.scans.append(scn)
            range_start = f.tell()
            # end of range


if __name__ == '__main__':
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    raw_file = RawFile()
    raw_file.get_file(os.path.join("..", "test", "test_data", "002.raw"))
    raw_file.parser_file()
