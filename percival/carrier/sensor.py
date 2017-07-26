'''
Created on 15 July 2016

:author: Alan Greer

A class representation for the Percival Sensor.

This class will maintain the sensor DACs, and apply using the buffer transfer
when requested.

TODO: This assumes the buffer has already been filled with values.  This
class could instead of taking the number of words, take the actual words and
fill the buffer itself.
'''
from __future__ import print_function

import logging

class SensorDac(object):
    """
    Represent a sensor DAC
    """
    def __init__(self, dac_ini):
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._log.debug("Sensor DAC created %s", dac_ini)
        self._config = dac_ini
        self._raw_value = 0

    @property
    def name(self):
        return self._config["Channel_name"]

    @property
    def buffer_index(self):
        return self._config["Buffer_index"]

    def set_value(self, value):
        self._log.debug("DAC [%s] value set to %d", self._config["Channel_name"], value)
        self._raw_value = value

    def to_buffer_word(self):
        # Raw value is ANDed with number of bits and offset
        bit_mask = (2 ** self._config["Bit_size"]) - 1
        buffer_value = self._raw_value & bit_mask
        buffer_value = buffer_value << self._config["Bit_offset"]
        self._log.debug("Buffer value returned %d", buffer_value)
        return buffer_value


class Sensor(object):
    """
    Represent the Percival Sensor.
    """
    def __init__(self, buffer_cmd):
        """
        Constructor

        :param buffer_cmd: Percival buffer command object
        :type  buffer: SensorBufferCommand
        """
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._buffer_cmd = buffer_cmd
        self._dacs = {}
        self._buffer_words = {}

    @property
    def dacs(self):
        return self._dacs

    def add_dac(self, dac_ini):
        """
        Add a DAC to the sensor set.
        :param dac_ini:
        :return:
        """
        # Create the SensorDAC object from the initialisation values
        dac = SensorDac(dac_ini)
        self._log.debug("Adding DAC [%s] to sensor", dac.name)
        self._dacs[dac.name] = dac
        # Keep a list of dac names for each buffer index
        if dac.buffer_index not in self._buffer_words:
            self._buffer_words[dac.buffer_index] = []

        # Append the name to the relevant buffer index store
        self._buffer_words[dac.buffer_index].append(dac.name)

    def set_dac(self, dac_name, value):
        """
        Set a DAC value ready for writing to the hardware.
        Sensor DAC values are written by buffer transfer so must all be set prior
        to a write
        :param dac_name:
        :param value:
        :return:
        """
        self._log.debug("Setting sensor DAC [%s] value: %d", dac_name, value)
        if dac_name in self._dacs:
            self._dacs[dac_name].set_value(value)

    def _generate_dac_words(self):
        # Create the set of words ready for the buffer write command
        words = []
        for index in sorted(self._buffer_words):
            word_value = 0
            for dac_name in self._buffer_words[index]:
                word_value += self._dacs[dac_name].to_buffer_word()

            words.append(word_value)
        return words

    def configuration_values_to_word(self, size, values):
        self._log.debug("Combining sensor values into 32 bit word")
        # Check how many values can be combined
        self._log.debug("Size of each value: %d", size)
        qty_values = 32 // size
        self._log.debug("Number of values that can fit into 32 bits: %d", qty_values)
        extra_shift = 32 % size
        self._log.debug("Extra shift required: %d", extra_shift)
        mask = 2**size - 1
        self._log.debug("Mask for values: %d", mask)
        if len(values) > qty_values:
            self._log.error("Too many sensor values to be stored in a 32 bit word")
            raise RuntimeError("Too many sensor values to be stored in a 32 bit word")
        # Extend the values if necessary
        if len(values) < qty_values:
            values = (values + [0] * qty_values)[:qty_values]

        value = 0
        for index in range(qty_values):
            value = (value << size) + (values[index] & mask)
        value <<= extra_shift
        return value

    def apply_dac_values(self):
        # Generate the words and write to the buffer
        # Send the appropriate buffer command
        words = self._generate_dac_words()
        self._log.debug("Applying sensor DAC values: %s", words)
        self._buffer_cmd.send_dacs_setup_cmd(words)

    def apply_configuration(self, config):
        if config:
            self._log.debug("Applying sensor configuration: %s", config)
            # We need to verify the configuration
            if 'H1' in config and 'H0' in config and 'G' in config:
                h1_values = config['H1']
                words = []
                while len(h1_values) > 9:
                    words.append(self.configuration_values_to_word(3, h1_values[0:10]))
                    h1_values = h1_values[10:]
                h0_values = h1_values + config['H0']
                while len(h0_values) > 9:
                    words.append(self.configuration_values_to_word(3, h0_values[0:10]))
                    h0_values = h0_values[10:]
                g_values = h0_values + config['G']
                while len(g_values) > 9:
                    words.append(self.configuration_values_to_word(3, g_values[0:10]))
                    g_values = g_values[10:]
                if len(g_values) > 0:
                    words.append(self.configuration_values_to_word(3, g_values))
                self._log.debug("Sensor configuration words: %s", words)
                self._buffer_cmd.send_configuration_setup_cmd(words)

    def apply_debug(self, debug):
        self._log.debug("Applying sensor debug: %s", debug)
        # We need to first verify the debug description
        if 'H1' in debug and 'H0' in debug and 'G' in debug:
            h1_values = debug['H1']
            words = []
            while len(h1_values) > 4:
                words.append(self.configuration_values_to_word(6, h1_values[0:5]))
                h1_values = h1_values[5:]
            h0_values = h1_values + debug['H0']
            while len(h0_values) > 4:
                words.append(self.configuration_values_to_word(6, h0_values[0:5]))
                h0_values = h0_values[5:]
            g_values = h0_values + debug['G']
            while len(g_values) > 4:
                words.append(self.configuration_values_to_word(6, g_values[0:5]))
                g_values = g_values[5:]
            if len(g_values) > 0:
                words.append(self.configuration_values_to_word(6, g_values))
            self._log.debug("Sensor debug words: %s", words)
            self._buffer_cmd.send_debug_setup_cmd(words)

    def apply_calibration(self, calibration):
        self._log.debug("Applying sensor calibration: %s", calibration)
        # We need to first verify the debug description
        # Expected format
        #
        # { H1 : { Cal1 : { Left : [],
        #                   Right: [] },
        #          Cal2 : { Left : [],
        #                   Right: [] },
        #          Cal3 : { Left : [],
        #                   Right: [] },
        #          Cal4 : { Left : [],
        #                   Right: [] },
        #        },
        #   H0 : { Cal1 : { Left : [],
        #                   Right: [] },
        #          Cal2 : { Left : [],
        #                   Right: [] },
        #          Cal3 : { Left : [],
        #                   Right: [] },
        #          Cal4 : { Left : [],
        #                   Right: [] },
        #        },
        #   G  : { Cal1 : { Left : [],
        #                   Right: [] },
        #          Cal2 : { Left : [],
        #                   Right: [] },
        #          Cal3 : { Left : [],
        #                   Right: [] },
        #          Cal4 : { Left : [],
        #                   Right: [] },
        #        }
        # }
        #
        data_words = []
        calibration_keys = ['H1', 'H0', 'G']
        calibration_set_names = ['Cal1', 'Cal2', 'Cal3', 'Cal4']
        if all(name in calibration_keys for name in calibration):
            for key in calibration_keys:
                calibration_set = calibration[key]
                if all(name in calibration_set_names for name in calibration_set):
                    calibration_set_1 = calibration_set['Cal1']
                    calibration_set_2 = calibration_set['Cal2']
                    calibration_set_3 = calibration_set['Cal3']
                    calibration_set_4 = calibration_set['Cal4']
                    col1_values = self.combine_9bit_lists_into_8bit_list(calibration_set_1['Right'],
                                                                         calibration_set_1['Left'])
                    col2_values = self.combine_9bit_lists_into_8bit_list(calibration_set_2['Right'],
                                                                         calibration_set_2['Left'])
                    col3_values = self.combine_9bit_lists_into_8bit_list(calibration_set_3['Right'],
                                                                         calibration_set_3['Left'])
                    col4_values = self.combine_9bit_lists_into_8bit_list(calibration_set_4['Right'],
                                                                         calibration_set_4['Left'])
                    data_words = data_words + self.combine_8bit_lists_into_32bit_list(col1_values,
                                                                                      col2_values,
                                                                                      col3_values,
                                                                                      col4_values)
                    self._log.debug("Sensor calibration words: %s", data_words)
                    self._buffer_cmd.send_calibration_setup_cmd(data_words)
                else:
                    self._log.error("Unable to find calibration targets %s in set %s", calibration_set_names, key)
                    raise RuntimeError("Unable to find calibration targets %s in set %s", calibration_set_names, key)
        else:
            self._log.error("Unable to find calibration sets %s within calibration object", calibration_keys)
            raise RuntimeError("Unable to find calibration sets %s within calibration object", calibration_keys)

    def combine_9bit_lists_into_8bit_list(self, list1, list2):
        self._log.debug("Combining 2 x 9 bit lists: %s and %s", list1, list2)
        # This method takes two lists of 9 bit values and creates a single list of 8 bit values
        # First interleave the two lists
        interleaved = [val for pair in zip(list1, list2) for val in pair]
        # Now loop over the new list and convert into 8 bit
        values = []
        bit = 0
        value = 0
        for val in interleaved:
            bits_left = 9
            while bits_left > 0:
                value <<= 1
                value += (val & (1<<(bits_left-1))) >> (bits_left-1)
                bit += 1
                if bit == 8:
                    # Filled up 8 bit value so add it
                    values.append(value)
                    value = 0
                    bit = 0
                bits_left -= 1
        return values

    def combine_8bit_lists_into_32bit_list(self, list1, list2, list3, list4):
        self._log.debug("Combining 4 x 8 bit lists: %s, %s, %s and %s", list1, list2, list3, list4)
        # Verify all lists are the same length
        if len(list1) != len(list2) or len(list2) != len(list3) or len(list3) != len(list4):
            self._log.error("Inconsistent list sizes, cannot combine")
            raise RuntimeError("Inconsistent list sizes, cannot combine")

        values = []
        for index in range(len(list1)):
            value = ((list1[index]&0xFF)<<24) + ((list2[index]&0xFF)<<16) + ((list3[index]&0xFF)<<8) + (list4[index]&0xFF)
            values.append(value)

        self._log.error("Calculated 32 bit values: %s", values)

        return values
