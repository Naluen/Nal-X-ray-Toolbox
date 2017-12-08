from unittest import TestCase
import h5py
from module import H5File
import numpy as np
import os


class TestH5File(TestCase):

    def test_property(self):
        assert H5File.H5File().name == 'H5File'
        assert H5File.H5File().supp_type == '.h5'

