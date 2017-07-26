'''
Created on 17 July 2017

@author: gnx91527
'''

from __future__ import unicode_literals, absolute_import

import unittest, sys, logging
from mock import MagicMock, call
from builtins import bytes

import percival.carrier.const as const
from percival.carrier.buffer import BufferCommand, SensorBufferCommand
from percival.carrier.txrx import TxMessage


class TestBuffer(unittest.TestCase):

    def setUp(self):
        # Perform any setup here
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.DEBUG)
        self.txrx = MagicMock()

    def TestSimpleBufferCommand(self):

        self.buffer = BufferCommand(self.txrx, const.BufferTarget.mezzanine_board_A)
        cmd = self.buffer._get_command_msg(const.BufferCmd.no_operation)
        self.assertEqual(cmd, TxMessage(bytes("\x03\x3B\x00\x00\x00\x00", encoding="latin-1"), expect_eom=False))

        cmd = self.buffer._get_command_msg(const.BufferCmd.read)
        self.assertEqual(cmd, TxMessage(bytes("\x03\x3B\x11\x00\x00\x00", encoding="latin-1"),
                                        num_response_msg=2,
                                        expect_eom=False))

        cmd = self.buffer._get_command_msg(const.BufferCmd.write, 0x5, 0x3A)
        self.assertEqual(cmd, TxMessage(bytes("\x03\x3B\x10\x05\x00\x3A", encoding="latin-1"),
                                        num_response_msg=2,
                                        expect_eom=False))

        self.txrx.send_recv_message = MagicMock(return_value=[(0x00000001, 0x00000002)])
        response = self.buffer.cmd_no_operation()
        self.assertEqual(response, [(0x00000001, 0x00000002)])

        self.txrx.send_recv_message = MagicMock(return_value=[(0x00000003, 0x00000004)])
        response = self.buffer.send_command(const.BufferCmd.write, 0x1, 0x2)
        self.assertEqual(response, [(0x00000003, 0x00000004)])

    def TestSensorBufferCommand(self):
        #
        # Sensor DAC command
        #
        self.txrx.send_recv = MagicMock()
        self.txrx.send_recv_message = MagicMock(return_value=[(0xFFFF, 0xABBABAC1), (0xFFF3, 0xABBA3333)])
        self.buffer = SensorBufferCommand(self.txrx)
        self.buffer.send_dacs_setup_cmd([0x00000001, 0x00000002, 0x00000003, 0x00000004])
        calls = self.txrx.send_recv_message.mock_calls
        # Assert that the data words were written into the buffer
        self.assertEqual(calls[0], call(TxMessage(bytes("\x02\xFA\x00\x00\x00\x01", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[1], call(TxMessage(bytes("\x02\xFB\x00\x00\x00\x02", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[2], call(TxMessage(bytes("\x02\xFC\x00\x00\x00\x03", encoding="latin-1"),
                                                  num_response_msg = 1,
                                                  expect_eom = False)))
        self.assertEqual(calls[3], call(TxMessage(bytes("\x02\xFD\x00\x00\x00\x04", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))

        #
        # Sensor Config command
        #
        # Generate the words required to submit a sensor config command
        words = range(0,144)
        std_reply = (0xFFFF, 0xABBABAC1)
        sensor_reply = (0xFFF3, 0xABBA3333)
        # Create the returned expected responses for the config command
        return_values = []
        for index in range(64):
            return_values.append(std_reply)
        # Iteration 1 null command standard response
        return_values.append(std_reply)
        # Iteration 1 sensor response
        return_values.append([std_reply, sensor_reply])
        for index in range(64):
            return_values.append(std_reply)
        # Iteration 2 null command standard response
        return_values.append(std_reply)
        # Iteration 1 sensor response
        return_values.append([std_reply, sensor_reply])
        for index in range(16):
            return_values.append(std_reply)
        # Iteration 3 null command standard response
        return_values.append(std_reply)
        # Iteration 1 sensor response
        return_values.append([std_reply, sensor_reply])
        self.log.debug("Return values : %s", return_values)
        self.txrx.send_recv_message = MagicMock()
        self.txrx.send_recv_message.side_effect = return_values
        self.buffer.send_configuration_setup_cmd(words)
        # Verify that the correct calls were made to the txrx object for filling in the buffers
        calls = self.txrx.send_recv_message.mock_calls
        # Assert that the data words were written into the buffer
        self.assertEqual(calls[0], call(TxMessage(bytes("\x02\xFA\x00\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[1], call(TxMessage(bytes("\x02\xFB\x00\x00\x00\x01", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[2], call(TxMessage(bytes("\x02\xFC\x00\x00\x00\x02", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[3], call(TxMessage(bytes("\x02\xFD\x00\x00\x00\x03", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[4], call(TxMessage(bytes("\x02\xFE\x00\x00\x00\x04", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[5], call(TxMessage(bytes("\x02\xFF\x00\x00\x00\x05", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[6], call(TxMessage(bytes("\x03\x00\x00\x00\x00\x06", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[7], call(TxMessage(bytes("\x03\x01\x00\x00\x00\x07", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[8], call(TxMessage(bytes("\x03\x02\x00\x00\x00\x08", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[9], call(TxMessage(bytes("\x03\x03\x00\x00\x00\x09", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[72], call(TxMessage(bytes("\x03\x00\x00\x00\x00\x46", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[73], call(TxMessage(bytes("\x03\x01\x00\x00\x00\x47", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[74], call(TxMessage(bytes("\x03\x02\x00\x00\x00\x48", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[75], call(TxMessage(bytes("\x03\x03\x00\x00\x00\x49", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[76], call(TxMessage(bytes("\x03\x04\x00\x00\x00\x4A", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[77], call(TxMessage(bytes("\x03\x05\x00\x00\x00\x4B", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[78], call(TxMessage(bytes("\x03\x06\x00\x00\x00\x4C", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[79], call(TxMessage(bytes("\x03\x07\x00\x00\x00\x4D", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[80], call(TxMessage(bytes("\x03\x08\x00\x00\x00\x4E", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[81], call(TxMessage(bytes("\x03\x09\x00\x00\x00\x4F", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        # Verify that the correct calls were made to the txrx object for sending the buffer commands
        # Assert that the commands were sent in the correct order
        self.assertEqual(calls[64], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[65], call(TxMessage(bytes("\x03\x3B\x51\x00\x00\x01", encoding="latin-1"),
                                                  num_response_msg=2,
                                                  expect_eom=False)))
        self.assertEqual(calls[130], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[131], call(TxMessage(bytes("\x03\x3B\x51\x00\x00\x02", encoding="latin-1"),
                                                  num_response_msg=2,
                                                  expect_eom=False)))
        self.assertEqual(calls[148], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[149], call(TxMessage(bytes("\x03\x3B\x51\x00\x00\x03", encoding="latin-1"),
                                                  num_response_msg=2,
                                                  expect_eom=False)))

        #
        # Sensor calibration command
        #
        # Generate the words required to submit a sensor config command
        words = range(0,3240)
        std_reply = (0xFFFF, 0xABBABAC1)
        sensor_reply = (0xFFF3, 0xABBA3333)
        # Create the returned expected responses for the config command
        return_values = []
        for index in range(0,90):
            for index2 in range(36):
                return_values.append(std_reply)
            # Iterations 1-90 null command standard response
            return_values.append(std_reply)
            # Iterations 1-90 sensor response
            return_values.append([std_reply, sensor_reply])
        self.log.debug("Return values : %s", return_values)
        self.txrx.send_recv_message = MagicMock()
        self.txrx.send_recv_message.side_effect = return_values
        self.buffer.send_calibration_setup_cmd(words)
        # Verify that the correct calls were made to the txrx object for filling in the buffers
        calls = self.txrx.send_recv_message.mock_calls
        # Assert that the data words were written into the buffer
        self.assertEqual(calls[0], call(TxMessage(bytes("\x02\xFA\x00\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[1], call(TxMessage(bytes("\x02\xFB\x00\x00\x00\x01", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[2], call(TxMessage(bytes("\x02\xFC\x00\x00\x00\x02", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[3], call(TxMessage(bytes("\x02\xFD\x00\x00\x00\x03", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[4], call(TxMessage(bytes("\x02\xFE\x00\x00\x00\x04", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[5], call(TxMessage(bytes("\x02\xFF\x00\x00\x00\x05", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[6], call(TxMessage(bytes("\x03\x00\x00\x00\x00\x06", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[7], call(TxMessage(bytes("\x03\x01\x00\x00\x00\x07", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[8], call(TxMessage(bytes("\x03\x02\x00\x00\x00\x08", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[9], call(TxMessage(bytes("\x03\x03\x00\x00\x00\x09", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[72], call(TxMessage(bytes("\x03\x1C\x00\x00\x00\x46", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[73], call(TxMessage(bytes("\x03\x1D\x00\x00\x00\x47", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[76], call(TxMessage(bytes("\x02\xFA\x00\x00\x00\x48", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[77], call(TxMessage(bytes("\x02\xFB\x00\x00\x00\x49", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[78], call(TxMessage(bytes("\x02\xFC\x00\x00\x00\x4A", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[79], call(TxMessage(bytes("\x02\xFD\x00\x00\x00\x4B", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[80], call(TxMessage(bytes("\x02\xFE\x00\x00\x00\x4C", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[81], call(TxMessage(bytes("\x02\xFF\x00\x00\x00\x4D", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[82], call(TxMessage(bytes("\x03\x00\x00\x00\x00\x4E", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[83], call(TxMessage(bytes("\x03\x01\x00\x00\x00\x4F", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[3166], call(TxMessage(bytes("\x03\x06\x00\x00\x0B\xB8", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3167], call(TxMessage(bytes("\x03\x07\x00\x00\x0B\xB9", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3168], call(TxMessage(bytes("\x03\x08\x00\x00\x0B\xBA", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3169], call(TxMessage(bytes("\x03\x09\x00\x00\x0B\xBB", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3170], call(TxMessage(bytes("\x03\x0A\x00\x00\x0B\xBC", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3171], call(TxMessage(bytes("\x03\x0B\x00\x00\x0B\xBD", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3172], call(TxMessage(bytes("\x03\x0C\x00\x00\x0B\xBE", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3173], call(TxMessage(bytes("\x03\x0D\x00\x00\x0B\xBF", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3174], call(TxMessage(bytes("\x03\x0E\x00\x00\x0B\xC0", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[3175], call(TxMessage(bytes("\x03\x0F\x00\x00\x0B\xC1", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        # Verify that the correct calls were made to the txrx object for sending the buffer commands
        # Assert that the commands were sent in the correct order
        self.assertEqual(calls[36], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[37], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x01", encoding="latin-1"),
                                                   num_response_msg=2,
                                                   expect_eom=False)))
        self.assertEqual(calls[74], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                   num_response_msg=1,
                                                   expect_eom=False)))
        self.assertEqual(calls[75], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x02", encoding="latin-1"),
                                                   num_response_msg=2,
                                                   expect_eom=False)))
        self.assertEqual(calls[112], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                    num_response_msg=1,
                                                    expect_eom=False)))
        self.assertEqual(calls[113], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x03", encoding="latin-1"),
                                                    num_response_msg=2,
                                                    expect_eom=False)))
        self.assertEqual(calls[1556], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[1557], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x29", encoding="latin-1"),
                                                     num_response_msg=2,
                                                     expect_eom=False)))
        self.assertEqual(calls[1594], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[1595], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x2A", encoding="latin-1"),
                                                     num_response_msg=2,
                                                     expect_eom=False)))
        self.assertEqual(calls[1632], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                     num_response_msg=1,
                                                     expect_eom=False)))
        self.assertEqual(calls[1633], call(TxMessage(bytes("\x03\x3B\x52\x00\x00\x2B", encoding="latin-1"),
                                                     num_response_msg=2,
                                                     expect_eom=False)))

        # Verify incorrect number of values will generate an exception
        with self.assertRaises(RuntimeError):
            test_values = [1, 1]
            self.buffer.send_calibration_setup_cmd(test_values)

        #
        # Sensor Debug command
        #
        self.txrx.send_recv_message = MagicMock()
        std_reply = (0xFFFF, 0xABBABAC1)
        sensor_reply = (0xFFF3, 0xABBA3333)
        # Create the returned expected responses for the config command
        return_values = []
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append(std_reply)
        return_values.append([std_reply, sensor_reply])
        self.txrx.send_recv_message.side_effect = return_values

        self.buffer = SensorBufferCommand(self.txrx)
        self.buffer.send_debug_setup_cmd([0x00000001,
                                          0x00000002,
                                          0x00000003,
                                          0x00000004,
                                          0x00000005,
                                          0x00000006,
                                          0x00000007,
                                          0x00000008,
                                          0x00000009])
        calls = self.txrx.send_recv_message.mock_calls
        # Assert that the data words were written into the buffer
        self.assertEqual(calls[0], call(TxMessage(bytes("\x02\xFA\x00\x00\x00\x01", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[1], call(TxMessage(bytes("\x02\xFB\x00\x00\x00\x02", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[2], call(TxMessage(bytes("\x02\xFC\x00\x00\x00\x03", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[3], call(TxMessage(bytes("\x02\xFD\x00\x00\x00\x04", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[4], call(TxMessage(bytes("\x02\xFE\x00\x00\x00\x05", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[5], call(TxMessage(bytes("\x02\xFF\x00\x00\x00\x06", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[6], call(TxMessage(bytes("\x03\x00\x00\x00\x00\x07", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[7], call(TxMessage(bytes("\x03\x01\x00\x00\x00\x08", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[8], call(TxMessage(bytes("\x03\x02\x00\x00\x00\x09", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))

        # Verify that the correct calls were made to the txrx object for sending the buffer commands
        # Assert that the commands were sent in the correct order
        self.assertEqual(calls[9], call(TxMessage(bytes("\x03\x3B\x50\x00\x00\x00", encoding="latin-1"),
                                                  num_response_msg=1,
                                                  expect_eom=False)))
        self.assertEqual(calls[10], call(TxMessage(bytes("\x03\x3B\x54\x00\x00\x01", encoding="latin-1"),
                                                   num_response_msg=2,
                                                   expect_eom=False)))

        # Verify incorrect number of values will generate an exception
        with self.assertRaises(RuntimeError):
            test_values = [1, 1]
            self.buffer.send_debug_setup_cmd(test_values)
