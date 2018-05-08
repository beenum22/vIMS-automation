#!/usr/bin/env python

import time
import argparse
import sys
import logging.config
from src.settings import Settings
from src.utilities import Utilities
from src.ssh import SSHConnection
from src.stack import Stack
from src.vims import vIMS
import subprocess
import json

def main():
    parser = argparse.ArgumentParser(description='vIMS Automation')
    parser.add_argument("-s", "--settings_file",
                        help='vIMS deployment parameters .ini file',
                        required=True)
    parser.add_argument("--debug",
                        help="increase output verbosity",
                        action="store_true")
    args, ignore = parser.parse_known_args()
    try:
        logging.config.fileConfig(
            'logging_conf.ini', disable_existing_loggers=False)
        vims_logger = logging.getLogger()
        if args.debug:
            vims_logger.setLevel('DEBUG')
        vims = vIMS('clearwater-vIMS', 'clearwater-heat/clearwater.yaml', 'clearwater-heat/environment.yaml', args.settings_file)
        vims.setup_env()
    except IOError as err:
        sys.exit("Failed to create the log file. %s: %s" % (err.strerror, err.filename))
    except Exception as err:
        vims_logger.error(err)
        sys.exit("Exiting...")
    except KeyboardInterrupt:
        vims_logger.error("Interrupted. Exiting...")
        sys.exit()

if __name__ == '__main__':
    main()
