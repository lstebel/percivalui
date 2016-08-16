"""
Created on 20 May 2016

@author: Alan Greer
"""
from __future__ import print_function
import argparse

from percival.log import log
from percival.detector.standalone import PercivalStandalone


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--write", default="False", help="Write the initialisation configuration to the board")
    parser.add_argument("-c", "--control", default="tcp://127.0.0.1:8888", help="ZeroMQ control endpoint")
    parser.add_argument("-s", "--status", default="tcp://127.0.0.1:8889", help="ZeroMQ status endpoint")
    args = parser.parse_args()
    return args


def main():
    args = options()
    log.info(args)

    # Check if we need to initialise the hardware
    init = False
    if args.write.upper() == "TRUE":
        init = True

    # Create the stand alone device
    percival = PercivalStandalone(init)

    # Initialise the control endpoint
    percival.setup_control_channel(args.control)

    # Initialise the status endpoint
    percival.setup_status_channel(args.status)

    # Startup the IpcReactor
    percival.start_reactor()


if __name__ == '__main__':
    main()
