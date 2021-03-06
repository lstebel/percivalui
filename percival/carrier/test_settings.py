'''
Created on 13 June 2016

@author: gnx91527
'''
from __future__ import unicode_literals, absolute_import

import unittest, sys, logging
from mock import MagicMock
from builtins import bytes

from percival.detector.detector import PercivalParameters
from percival.carrier import const
from percival.carrier.settings import BoardSettings


class TestBoardSettings(unittest.TestCase):

    def setUp(self):
        # Perform any setup here
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.DEBUG)
        self.txrx = MagicMock()
        self.parameters = PercivalParameters()
        self.parameters.load_ini()

    def TestInitialiseBoardLeft(self):
        bs = BoardSettings(self.txrx, const.BoardTypes.left)
        bs.initialise_board(self.parameters)

    def TestInitialiseBoardBottom(self):
        bs = BoardSettings(self.txrx, const.BoardTypes.bottom)
        bs.initialise_board(self.parameters)

    def TestInitialiseBoardCarrier(self):
        bs = BoardSettings(self.txrx, const.BoardTypes.carrier)
        bs.initialise_board(self.parameters)

    def TestInitialiseBoardPlugin(self):
        bs = BoardSettings(self.txrx, const.BoardTypes.plugin)
        bs.initialise_board(self.parameters)
