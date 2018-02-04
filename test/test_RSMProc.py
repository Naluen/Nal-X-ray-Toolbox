import unittest
import logging
import os

from module.RSMProc import RSMProc
from module.RawFile import RawFile
from unittest import TestCase


class TestRMSProc(TestCase):
    logging.basicConfig(
        # filename=os.path.join(
        #     os.path.dirname(sys.argv[0]), 'log', __name__ + '.log'),
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    def test_plot(self):
        raw_file = RawFile()
        raw_file.get_file(os.path.join("test_data", "002.raw"))

        data, attr = raw_file.get_data()
        proc = RSMProc()
        proc.set_data(data, attr)
        proc.plot()