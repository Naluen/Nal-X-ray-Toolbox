import logging

import numpy as np

from module.Module import FileModule


class FltFile(FileModule):
    def __init__(self):
        super(FltFile, self).__init__()

    @property
    def name(self):
        return __name__.split('.')[-1]

    @property
    def supp_type(self):
        return ".flt",

    @staticmethod
    def decode_head(head_stuck):
        head_stuck = head_stuck.decode('windows-1252').split('\r\n')
        scan_dict = {}
        for i in head_stuck:
            if not i.startswith('[') and not len(i) == 0:
                try:
                    scan_dict[i.split('=')[0]] = i.split('=')[1]
                except (KeyError, IndexError):
                    pass
        return scan_dict

    def file2narray(self):
        logging.debug("Transform data to ndarray...")
        with open(self.file, 'rb') as fp:
            try_head = fp.read(500)
            try_scan_dict = self.decode_head(try_head)
            fp.seek(0, 0)
            stuck_size = (
                    int(try_scan_dict['ResolutionX']) *
                    int(try_scan_dict['ResolutionY']) *
                    4
            )
            head = fp.read()[0: -stuck_size]

            attr = self.decode_head(head)

            attr['Type'] = 'raw_afm'

            fp.seek(0, 0)
            raw_data = fp.read()[-stuck_size:]

            import struct

            unpacked_data_l = [struct.unpack('f', raw_data[k:k + 4])
                               for k in range(0, len(raw_data), 4)]
            data = [i[0] for i in unpacked_data_l]
            data = np.asarray(data).reshape(
                int(attr['ResolutionX']),
                int(attr['ResolutionY']))

        return data, attr
