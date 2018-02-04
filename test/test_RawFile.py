import unittest
import logging
import os

from module.RawFile import RawFile
from unittest import TestCase


class TestRawFile(TestCase):
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    def test_parser_file(self):
        RAW_FILE = RawFile()
        RAW_FILE.get_file(os.path.join("test_data", "002.raw"))
        META_HEADER, SCANS = RAW_FILE.parser_file()
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Meta Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in META_HEADER.items()
        ]))
        # ====================================================================
        assert META_HEADER['RANGE_CNT'] == 1501
        assert META_HEADER['FORMAT_VERSION'] == 'v3'
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Scan Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in SCANS[0].header.items()
        ]))
        # ====================================================================
        assert SCANS[0]._STEPPING_DRIVE_CODE in (129, 130)
        assert SCANS[0].TWOTHETA

        RAW_FILE = RawFile()
        RAW_FILE.get_file(os.path.join("test_data", "PF.raw"))
        META_HEADER, SCANS = RAW_FILE.parser_file()
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Meta Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in META_HEADER.items()
        ]))
        # ====================================================================
        assert META_HEADER['RANGE_CNT'] == 69
        assert META_HEADER['FORMAT_VERSION'] == 'v3'
        # ====================================================================
        logging.debug("=" * 36)
        logging.debug("Scan Header has been read.")
        logging.debug(os.linesep + "".join([
            "{0}: {1} {2}".format(k, v, os.linesep)
            for k, v in SCANS[0].header.items()
        ]))
        # ====================================================================
        assert SCANS[0]._STEPPING_DRIVE_CODE is 5
        assert SCANS[0].STEP_TIME == 1



    def test_file2narray(self):
        RAW_FILE = RawFile()
        RAW_FILE.get_file(os.path.join("test_data", "002.raw"))

        DATA, ATTR = RAW_FILE.get_data()

        assert DATA.shape == (1291, 154)

        RAW_FILE = RawFile()
        RAW_FILE.get_file(os.path.join("test_data", "PF.raw"))

        DATA, ATTR = RAW_FILE.get_data()

        assert ATTR['STEPPING_DRIVE1'] == "KHI"
        assert ATTR['STEPPING_DRIVE2'] == 'PHI'

    # def test_
