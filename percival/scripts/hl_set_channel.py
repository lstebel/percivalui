'''
Created on 17 May 2016

@author: gnx91527
'''
from __future__ import print_function

import sys
import argparse
import requests
import getpass
from datetime import datetime

from percival.log import log
from percival.scripts.util import PercivalClient


def options():
    desc = """Set a channel value on the Percival Carrier Board
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-a", "--address", action="store", default="127.0.0.1:8888",
                        help="Odin server address (default 127.0.0.1:8888)")
    channel_help = "Channel to set"
    parser.add_argument("-c", "--channel", action="store", help=channel_help)
    value_help = "Value to set"
    parser.add_argument("-v", "--value", action="store", default=0, help=value_help)
    wait_help = "Wait for the command to complete (default true)"
    parser.add_argument("-w", "--wait", action="store", default="true", help=wait_help)
    args = parser.parse_args()
    return args


def main():
    args = options()
    log.info(args)

    data = {
               'channel': args.channel,
               'value': args.value
           }

    pc = PercivalClient(args.address)
    result = pc.send_command('cmd_set_channel',
                             'hl_set_channel.py',
                             arguments=data,
                             wait=(args.wait.lower() == "true"))
    log.info("Response: %s", result)


if __name__ == '__main__':
    main()
