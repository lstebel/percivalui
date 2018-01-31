'''
Created on 31 Jan 2018

@author: gnx91527
'''
from __future__ import print_function

import sys
import argparse

from percival.log import log
from percival.carrier import const
from percival.carrier.registers import UARTRegister
from percival.scripts.util import PercivalClient

system_settings = [name for name in UARTRegister(const.SYSTEM_SETTINGS).fields.map_fields]
system_settings.sort()
system_settings = "\n\t".join(system_settings)


def options():
    desc = """Send a System Command to the Percival Carrier Board
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-a", "--address", action="store", default="127.0.0.1:8888",
                        help="Odin server address (default 127.0.0.1:8888)")
    action_help = "System setting to set. Valid settings are: %s" % system_settings
    parser.add_argument("-s", "--setting", action="store", default="ACQUISTION_Acquisition_mode", help=action_help)
    value_help = "The value to set (default 0)"
    parser.add_argument("-v", "--value", action="store", default=0, help=value_help)
    wait_help = "Wait for the command to complete (default true)"
    parser.add_argument("-w", "--wait", action="store", default="true", help=wait_help)
    args = parser.parse_args()
    return args


def main():
    return_value = 0
    args = options()
    log.info(args)

    data = {
        'setting': args.setting,
        'value': args.value
    }

    pc = PercivalClient(args.address)
    result = pc.send_command('cmd_system_setting', 'hl_set_system_setting.py', arguments=data)
    log.info("Response: %s", result)
    if args.wait.lower() == "true":
        result = pc.wait_for_command_completion(0.2)

    if result['response'] == 'Failed':
        return_value = -1

    return return_value


if __name__ == '__main__':
    main()
