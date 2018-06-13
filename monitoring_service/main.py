#!/usr/bin/env python
from monitor import Monitor
from utilities import Utilities
import logging
import time
import logging.config
import threading
import sys

def main():
    try:
        Utilities._create_dir("/var/log/vims_cluster")
        logging.config.fileConfig(
            'logging.ini', disable_existing_loggers=False)
        threads = []
        monitor = Monitor('config.ini')
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