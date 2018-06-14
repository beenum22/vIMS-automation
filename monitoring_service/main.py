#!/usr/bin/env python

from src.monitor import Monitor
from src.utilities import Utilities
import logging
import time
import logging.config
import threading
import sys
import argparse

def main():
    try:
        Utilities._create_dir("/var/log/vims_cluster")
        parser = argparse.ArgumentParser(description='vIMS Cluster monitoring service')
        parser.add_argument("-c", "--config",
                            help='Service parmeters configuration file',
                            required=True)
        parser.add_argument("-l", "--logging",
                            help='Service logging configuration file',
                            required=True)
        args, ignore = parser.parse_known_args()
        logging.config.fileConfig(
            args.logging, disable_existing_loggers=False)
        threads = []
        monitor = Monitor(args.config)
        logger = logging.getLogger()
        cluster = threading.Thread(target=monitor.update_cluster)
        bono = threading.Thread(target=monitor.monitor_bono)
        sprout = threading.Thread(target=monitor.monitor_sprout)
        dime = threading.Thread(target=monitor.monitor_dime)
        vellum = threading.Thread(target=monitor.monitor_vellum)
        homer = threading.Thread(target=monitor.monitor_homer)
        cluster.daemon = True
        bono.daemon = True
        sprout.daemon = True
        dime.daemon = True
        vellum.daemon = True
        homer.daemon = True
        logger.info("Starting the cluster monitoring thread.")
        cluster.start()
        logger.info("Starting the Bono cluster monitoring thread.")
        bono.start()
        logger.info("Starting the Sprout cluster monitoring thread.")
        sprout.start()
        logger.info("Starting the Dime cluster monitoring thread.")
        dime.start()
        logger.info("Starting the Vellum cluster monitoring thread.")
        vellum.start()
        logger.info("Starting the Homer cluster monitoring thread.")
        homer.start()        
        threads.append(cluster)
        threads.append(bono)
        threads.append(sprout)
        threads.append(dime)
        threads.append(vellum)
        threads.append(homer)
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt.")
        logger.info("Exiting...")
        sys.exit()

if __name__ == '__main__':
    main()