#!/usr/bin/env python

import etcd
import logging
import sys
import re
import time
# from pysnmp.entity.rfc3413.oneliner import cmdgen
# from pysnmp.hlapi import *
from easysnmp import Session, exceptions
from utilities import Utilities
import influxdb
import threading

# BONO OIDS
# scopeCurrent5MinutePeriod."node" : 4.110.111.100.101

# bonoConnectedClients : .1.2.826.0.1.1578918.9.2.1.0
# bonoLatencyCount : .1.2.826.0.1.1578918.9.2.2.1.7.2.4.110.111.100.101
# bonoSproutConnectionCount = .1.2.826.0.1.1578918.9.2.3.1.1.3.1.4.<sprout_sig_ip>
# bonoIncomingRequestsCount : .1.2.826.0.1.1578918.9.2.4.1.3.2.4.110.111.100.101
# bonoRejectedOverloadCount : .1.2.826.0.1.1578918.9.2.5.1.3.2.4.110.111.100.101
# bonoQueueSizeAverage : .1.2.826.0.1.1578918.9.2.6.1.3.2.4.110.111.100.101

# SPROUT OIDS
# sproutLatencyAverage : .1.2.826.0.1.1578918.9.3.1.1.3.2.4.110.111.100.101
# sproutHomerConnectionCount: Not found
# sproutHomesteadConnectionCount: Not found
# sproutIncomingRequestsCount : .1.2.826.0.1.1578918.9.3.6.1.3.2.4.110.111.100.101
# sproutRejectedOverloadCount : .1.2.826.0.1.1578918.9.3.7.1.3.2.4.110.111.100.101
# sproutQueueSizeAverage : .1.2.826.0.1.1578918.9.3.8.1.3.2.4.110.111.100.101
#

SYSDESCR_OID = '.1.3.6.1.2.1.1.1.0'
BONO_OIDS = ['.1.2.826.0.1.1578918.9.2.1.0',
             '.1.2.826.0.1.1578918.9.2.2.1.7.2.4.110.111.100.101',
             '.1.2.826.0.1.1578918.9.2.2.1.7.2'
             ]
INFLUX_USER = 'root'
INFLUX_PASSWORD = 'root'
INFLUX_PORT = '8086'
INFLUX_DB = 'telegraf'
INFLUX_HOST = '127.0.0.1'
SPROUT_OIDS = []

BONO_UPPER_THRESHOLDS = {
        'bonoIncomingRequestsCount': 100,
        'bonoConnectedClients': 100,
        'bonoRejectedOverloadCount': 100,
        'bonoQueueSizeAverage': 100,
        'bonoLatencyCount': 100
        }
BONO_LOWER_THRESHOLDS = {
        'bonoIncomingRequestsCount': 5,
        'bonoConnectedClients': 0,
        'bonoQueueSizeAverage': 0,
        }

BONO_WEBHOOKS = {'scaleup': None, 'scaledown': None}

logger = logging.getLogger()


class Monitor(object):

    def __init__(self, etcd_ip, webhooks, etcd_port=4000):
        self.etcd_ip = etcd_ip
        self.etcd_port = etcd_port
        self.webhooks = webhooks
        self.nodes = {'bono': {}, 'dime': {},
                      'sprout': {}, 'vellum': {}, 'homer': {}, 'node_list': []}
        self.influx_client = influxdb.InfluxDBClient(
            INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD, INFLUX_DB)

    def start_monitoring(self):
        # Start update_nodes thread in the background
        # Start a while loop which repeats all the steps
        pass

    def _etcd_client(self):
        try:
            client = etcd.Client(self.etcd_ip, port=self.etcd_port)
            client.cluster_version
            return client
        except etcd.EtcdConnectionFailed as err:
            logger.debug(err)
            logger.error("Failed to connect to the etcd cluster")
            logger.error("Exiting...")
            sys.exit()

    def update_cluster(self):
        self.update_nodes()
        self.update_telegraf_configs()

    def update_nodes(self):
        tmp_nodes = {'bono': {}, 'dime': {}, 'sprout': {},
            'vellum': {}, 'homer': {}, 'node_list': []}
        client = self._etcd_client()
        nodes = client.machines
        for n in nodes:
            ip = re.search(r"[^(http:\/\/)]+", n).group(0)
            hostname = self._get_hostname(ip)
            #print "HOSTNAME: %s - IP: %s" % (hostname, ip)
            if hostname != None:
                tmp_nodes['node_list'].append(hostname)
                if 'bono' in hostname:
                    tmp_nodes['bono'][hostname] = ip
                elif 'sprout' in hostname:
                    tmp_nodes['sprout'][hostname] = ip
                elif 'vellum' in hostname:
                    tmp_nodes['vellum'][hostname] = ip
                elif 'dime' in hostname:
                    tmp_nodes['dime'][hostname] = ip
                elif 'homer' in hostname:
                    tmp_nodes['homer'][hostname] = ip
        self.nodes = tmp_nodes

    def telegraf_config(self, path='/etc/telegraf/telegraf.d'):
        '''
        logger.debug("Fetching current monitored nodes from telegraf.")
        current_files = Utilities.run_cmd('ls %s' % path)[0].split('\n')
        current_files = [x.strip('.conf') for x in current_files]
        print "Files: %s" % current_files
        print "Nodes: %s" % self.nodes['node_list']
        new_nodes = list(set(self.nodes['node_list']) - set(current_files))
        old_nodes = list(set(current_files) - set(self.nodes['node_list']))
        if old_nodes == ['']:
            old_nodes.pop(0)
        if new_nodes == ['']:
            new_nodes.pop(0)
        '''
        logger.debug("New nodes: %s", new_nodes)
        logger.debug("Old nodes: %s", old_nodes)
        print "NEW: %s " % new_nodes
        print "OLD: %s" % old_nodes
        '''
        if old_nodes == [] and new_nodes == []:
            logger.info("No updates in the cluster. Skipping...")
            return False
        for node in new_nodes:
            logger.info("Adding new nodes to the telegraf.")
            self.add_telegraf_configs(node, path)
        for node in old_nodes:
            logger.info("Removing old nodes from the telegraf.")
            self.remove_telegraf_config(node, path)
        return True
        '''

    def update_telegraf_configs(self, path='/etc/telegraf/telegraf.d'):
        self.validate_telegraf_configs()
        new_nodes, old_nodes = self.get_node_lists(path)
        if old_nodes == [] and new_nodes == []:
            logger.info("No updates in the cluster. Skipping...")
            return False
        for node in new_nodes:
            logger.info("Adding new nodes to the telegraf.")
            self.add_telegraf_configs(node, path)
        for node in old_nodes:
            logger.info("Removing old nodes from the telegraf.")
            self.remove_telegraf_config(node, path)
        return True

    def get_node_lists(self, path):
        logger.debug("Fetching current monitored nodes from telegraf.")
        current_files = Utilities.run_cmd('ls %s' % path)[0].split('\n')
        current_files = [x.strip('.conf') for x in current_files]
        print "Files: %s" % current_files
        print "Nodes: %s" % self.nodes['node_list']
        new_nodes = list(set(self.nodes['node_list']) - set(current_files))
        old_nodes = list(set(current_files) - set(self.nodes['node_list']))
        logger.debug("New nodes: %s", new_nodes)
        logger.debug("Old nodes: %s", old_nodes)
        print "NEW: %s " % new_nodes
        print "OLD: %s" % old_nodes
        if old_nodes == ['']:
            old_nodes.pop(0)
        if new_nodes == ['']:
            new_nodes.pop(0)
        return new_nodes, old_nodes

    def validate_telegraf_configs(self, sample_path="/root/monitoring_data"):
        try:
            logger.debug("Validating sample telegraf configs...")
            assert Utilities.check_file(sample_path+'/bono_sample_snmp.conf'), "Bono SNMP sample file does not exist."
            assert Utilities.check_file(sample_path+'/sprout_sample_snmp.conf'), "Sprout SNMP sample file does not exist."
            assert Utilities.check_file(sample_path+'/sample_snmp.conf'), "Generic SNMP sample file does not exist."
        except AssertionError as err:
            logger.error(err)
            logger.error("Validation failed.")
            raise

    def create_telegraf_config(self, sample_path, conf_path, node, ip):
        Utilities.run_cmd(
            'cp %s %s/%s.conf' % (sample_path, conf_path, node))
        Utilities.run_cmd("sed -i s/<agent_ip:agent_port>/%s:161/g %s/%s.conf" %
                          (ip, conf_path, node))
        Utilities.run_cmd(
            "sed -i s/<agent_hostname>/%s/g %s/%s.conf" % (node, conf_path, node))

    def add_telegraf_configs(self, node, conf_path, sample_path="/root/monitoring_data"):
        if node in self.nodes['bono'].keys():
            self.create_telegraf_config(sample_path+'/bono_sample_snmp.conf', conf_path, node, self.nodes['bono'][node])
            #Utilities.run_cmd(
            #    'cp %s/bono_sample_snmp.conf %s/%s.conf' % (sample_path, conf_path, node))
            # print '%s -i s~<agent_ip:agent_port>~%s:161~g %s/%s.conf' % (Utilities.get_package_path('sed'), self.nodes['bono'][node], conf_path, node)
            #Utilities.run_cmd('%s -i s~<agent_ip:agent_port>~%s:161~g %s/%s.conf' % (Utilities.get_package_path('sed'), self.nodes['bono'][node], conf_path, node))
            # print '%s -i s~<agent_hostname>~%s~g %s/%s.conf' % (Utilities.get_package_path('sed'), node, conf_path, node)
            #Utilities.run_cmd('%s -i s~<agent_hostname>~%s~g %s/%s.conf' % (Utilities.get_package_path('sed'), node, conf_path, node))
        elif node in self.nodes['sprout'].keys():
            self.create_telegraf_config(sample_path+'/sprout_sample_snmp.conf', conf_path, node, self.nodes['sprout'][node])
        elif node in self.nodes['dime'].keys():
            self.create_telegraf_config(sample_path+'/sample_snmp.conf', conf_path, node, self.nodes['dime'][node])
        elif node in self.nodes['homer'].keys():
            self.create_telegraf_config(sample_path+'/sample_snmp.conf', conf_path, node, self.nodes['homer'][node])
        elif node in self.nodes['vellum'].keys():
            self.create_telegraf_config(sample_path+'/sample_snmp.conf', conf_path, node, self.nodes['vellum'][node])
        #else:
        #    self.create_telegraf_config(sample_path+'/sample_snmp.conf', conf_path, node)
            #Utilities.run_cmd(
            #    'cp %s/sprout_sample_snmp.conf %s/%s.conf' % (sample_path, conf_path, node))
            #Utilities.run_cmd("sed -i s/<agent_ip:agent_port>/%s:161/g %s/%s.conf" %
            #                  (self.nodes['sprout'][node], conf_path, node))
            #Utilities.run_cmd(
            #    "sed -i s/<agent_hostname>/%s/g %s/%s.conf" % (node, conf_path, node))

    def remove_telegraf_config(self, node, conf_path):
        print Utilities.run_cmd('rm %s/%s.conf' % (conf_path, node))

    def _get_hostname(self, host):
        value = self._poll_oid(host, SYSDESCR_OID)
        r = re.search(r'\w+\D[a-zA-Z0-9]+.(xflowresearch.com)', str(value))
        if r:
            return r.group(0)
        else:
            return None

    def _poll_oid(self, host, oid):
        try:
            session = Session(hostname=host, community='clearwater', version=2)
            return session.get(oid).value
        except exceptions.EasySNMPTimeoutError:
            logger.error("SNMP request timeout. Unable to access '%s'.", host)
            return None

    def _query_latest_influx(self, node):
        try:
            query = 'select last(*) from "%s";' % node
            logger.debug("Querying '%s' for latest SNMP stats")
            return list(self.influx_client.query(query).get_points())[0]
        except:
            logger.error("Failed to query '%s'", node)

    def trigger_alarm(self, alarm):
        pass

    def check_upper_threshold(self, output, threshold, alarm):
        try:
            assert output < threshold, trigger_alarm(alarm)
        except AssertionError:
            logger.info("Threshold hit. %s >= %s. Scaling Up...", output, threshold)

    def check_down_threshold(self, output, threshold, alarm):
        try:
            assert output > threshold, trigger_alarm(alarm)
        except AssertionError:
            logger.info("Threshold hit. %s <= %s. Scaling Down...", output, threshold)

    def bono_monitor(self):
        while True:
            for node in self.nodes['bono']:
                result = self._query_latest_influx(node)
                for t in BONO_UPPER_THRESHOLDS.keys():
                    self.check_upper_threshold(result['last_'+t], BONO_UPPER_THRESHOLDS[t], BONO_WEBHOOKS['scaleup'])
                for t in BONO_LOWER_THRESHOLDS.keys():
                    self.check_upper_threshold(result['last_'+t], BONO_DOWN_THRESHOLDS[t], BONO_WEBHOOKS['scaledown'])
            time.sleep(120)
