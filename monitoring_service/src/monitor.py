import etcd
import logging
import sys
import re
import time
from easysnmp import Session, exceptions
from utilities import Utilities
from settings import Settings
import influxdb
import threading

SYSDESCR_OID = '.1.3.6.1.2.1.1.1.0'
MONITOR_DELAY = 120
UPDATE_DELAY = 50

cluster_logger = logging.getLogger('cluster')
alarm_logger = logging.getLogger('alarm')


class Monitor(object):

    def __init__(self, config_file):
        self.cluster_status = False
        self.settings = Settings(config_file)
        self.settings.parse_settings_file()
        self.nodes = {'bono': {}, 'dime': {},
                      'sprout': {}, 'vellum': {}, 'homer': {}, 'node_list': []}
        self.influx_client = influxdb.InfluxDBClient(
            self.settings.influxdb['host'],
            self.settings.influxdb['port'],
            self.settings.influxdb['user'],
            self.settings.influxdb['password'],
            self.settings.influxdb['db']
        )

    def _etcd_client(self):
        try:
            client = etcd.Client(self.settings.etcd[
                                 'ip'], port=int(self.settings.etcd['port']))
            client.cluster_version
            return client
        except etcd.EtcdConnectionFailed as err:
            cluster_logger.debug(err)
            cluster_logger.error("Failed to connect to the etcd cluster")
            cluster_logger.error("Exiting...")
            sys.exit()

    def update_cluster(self):
        while True:
            self.cluster_status = False
            self.update_nodes()
            self.update_telegraf_configs()
            self.cluster_status = True
            cluster_logger.info(
                "Cluster monitor going to sleep for %d seconds...", UPDATE_DELAY)
            time.sleep(UPDATE_DELAY)

    def update_nodes(self):
        tmp_nodes = {'bono': {}, 'dime': {}, 'sprout': {},
                     'vellum': {}, 'homer': {}, 'node_list': []}
        client = self._etcd_client()
        nodes = client.machines
        for n in nodes:
            ip = re.search(r"[^(http:\/\/)]+", n).group(0)
            hostname = self._get_hostname(ip)
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

    def update_telegraf_configs(self, path='/etc/telegraf/telegraf.d'):
        self.validate_telegraf_configs()
        new_nodes, old_nodes = self.get_node_lists(path)
        if old_nodes == [] and new_nodes == []:
            cluster_logger.info("No updates in the cluster. Skipping...")
            return False
        for node in new_nodes:
            cluster_logger.info(
                "Adding new node: '%s' agent to the telegraf.", node)
            self.add_telegraf_configs(node, path)
        for node in old_nodes:
            cluster_logger.info("Removing old nodes from the telegraf.")
            self.remove_telegraf_config(node, path)
        if new_nodes or old_nodes:
            cluster_logger.info("Restarting telegraf service")
            Utilities.run_cmd("service telegraf restart")
        return True

    def get_node_lists(self, path):
        cluster_logger.debug("Fetching current monitored nodes from telegraf.")
        current_files = Utilities.run_cmd('ls %s' % path)[0].split('\n')
        current_files = [x.strip('.conf') for x in current_files]
        cluster_logger.debug("Current config files: %s", current_files)
        cluster_logger.debug("Discovered nodes: %s", self.nodes['node_list'])
        new_nodes = list(set(self.nodes['node_list']) - set(current_files))
        old_nodes = list(set(current_files) - set(self.nodes['node_list']))
        cluster_logger.debug("New nodes: %s", new_nodes)
        cluster_logger.debug("Old nodes: %s", old_nodes)
        if old_nodes == ['']:
            old_nodes.pop(0)
        if new_nodes == ['']:
            new_nodes.pop(0)
        return new_nodes, old_nodes

    def validate_telegraf_configs(self, sample_path="/root/monitoring_data/samples"):
        try:
            cluster_logger.debug("Validating sample telegraf configs...")
            assert Utilities.check_file(
                sample_path + '/bono_sample_snmp.conf'), "Bono SNMP sample file does not exist."
            assert Utilities.check_file(
                sample_path + '/sprout_sample_snmp.conf'), "Sprout SNMP sample file does not exist."
            assert Utilities.check_file(
                sample_path + '/sample_snmp.conf'), "Generic SNMP sample file does not exist."
        except AssertionError as err:
            cluster_logger.error(err)
            cluster_logger.error("Validation failed.")
            raise

    def create_telegraf_config(self, sample_path, conf_path, node, ip):
        Utilities.run_cmd(
            'cp %s %s/%s.conf' % (sample_path, conf_path, node))
        Utilities.run_cmd("sed -i s/<agent_ip:agent_port>/%s:161/g %s/%s.conf" %
                          (ip, conf_path, node))
        Utilities.run_cmd(
            "sed -i s/<agent_hostname>/%s/g %s/%s.conf" % (node, conf_path, node))

    def add_telegraf_configs(self, node, conf_path, sample_path="/root/monitoring_data/samples"):
        if node in self.nodes['bono'].keys():
            self.create_telegraf_config(
                sample_path + '/bono_sample_snmp.conf', conf_path, node, self.nodes['bono'][node])
        elif node in self.nodes['sprout'].keys():
            self.create_telegraf_config(
                sample_path + '/sprout_sample_snmp.conf', conf_path, node, self.nodes['sprout'][node])
        elif node in self.nodes['dime'].keys():
            self.create_telegraf_config(
                sample_path + '/sample_snmp.conf', conf_path, node, self.nodes['dime'][node])
        elif node in self.nodes['homer'].keys():
            self.create_telegraf_config(
                sample_path + '/sample_snmp.conf', conf_path, node, self.nodes['homer'][node])
        elif node in self.nodes['vellum'].keys():
            self.create_telegraf_config(
                sample_path + '/sample_snmp.conf', conf_path, node, self.nodes['vellum'][node])

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
            cluster_logger.warning(
                "SNMP request timeout. Unable to access '%s'", host)
            return None

    def _query_latest_influx(self, node):
        try:
            query = 'select last(*) from "%s";' % node
            alarm_logger.debug("Querying '%s' for latest SNMP stats")
            return list(self.influx_client.query(query).get_points())[0]
        except:
            alarm_logger.error("Failed to query '%s'", node)

    def trigger_alarm(self, alarm, parameter):
        alarm_logger.info("Alarm trigger request due to '%s'...", parameter)
        alarm_logger.info("Triggering alarm...")
        Utilities.run_cmd("curl -XPOST -i %s" % alarm)

    def check_upper_threshold(self, output, threshold, alarm, parameter):
        try:
            if threshold.isdigit():
                threshold = int(threshold)
                output = int(output)
            else:
                threshold = float(threshold)
                output = float(output)
            assert output < threshold, self.trigger_alarm(alarm, parameter)
        except AssertionError:
            alarm_logger.info("Threshold hit. %s >= %s. Scaling Up...",
                              output, threshold)

    def check_down_threshold(self, output, threshold, alarm, parameter):
        try:
            if threshold.isdigit():
                threshold = int(threshold)
                output = int(output)
            else:
                threshold = float(threshold)
                output = float(output)
            assert output > threshold, self.trigger_alarm(alarm, parameter)
        except AssertionError:
            alarm_logger.info("Threshold hit. %s <= %s. Scaling Down...",
                              output, threshold)

    def monitor_bono(self):
        alarm_logger.info("Monitoring Bono Cluster...")
        while True:
            if self.cluster_status is True:
                for node in self.nodes['bono']:
                    result = self._query_latest_influx(node)
                    for t in self.settings.bono_upper_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) upper threshold for Bono-node: %s", t, result['last_' + t], self.settings.bono_upper_thresholds[t], node)
                        self.check_upper_threshold(
                            result['last_' + t], self.settings.bono_upper_thresholds[t], self.settings.webhooks['bono_scaleup'], t)
                    for t in self.settings.bono_lower_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) lower threshold for Bono-node: %s", t, result['last_' + t], self.settings.bono_lower_thresholds[t], node)
                        self.check_down_threshold(
                            result['last_' + t], self.settings.bono_lower_thresholds[t], self.settings.webhooks['bono_scaledown'], t)
            else:
                alarm_logger.warning(
                    "vIMS Cluster info is updating. Skipping Bono Cluster monitoring...")
            alarm_logger.info(
                "Bono Cluster monitor sleeping for %d seconds...", MONITOR_DELAY)
            time.sleep(MONITOR_DELAY)

    def monitor_sprout(self):
        alarm_logger.info("Monitoring Sprout Cluster...")
        while True:
            if self.cluster_status is True:
                for node in self.nodes['sprout']:
                    result = self._query_latest_influx(node)
                    for t in self.settings.sprout_upper_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) upper threshold for Sprout-node: %s", t, result['last_' + t], self.settings.sprout_upper_thresholds[t], node)
                        self.check_upper_threshold(
                            result['last_' + t], self.settings.sprout_upper_thresholds[t], self.settings.webhooks['sprout_scaleup'], t)
                    for t in self.settings.sprout_lower_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) lower threshold for Sprout-node: %s", t, result['last_' + t], self.settings.sprout_lower_thresholds[t], node)
                        self.check_down_threshold(
                            result['last_' + t], self.settings.sprout_lower_thresholds[t], self.settings.webhooks['sprout_scaledown'], t)
            else:
                alarm_logger.warning(
                    "vIMS Cluster info is updating. Skipping Sprout Cluster monitoring...")
            alarm_logger.info(
                "Sprout Cluster monitor sleeping for %d seconds...", MONITOR_DELAY)
            time.sleep(MONITOR_DELAY)

    def monitor_dime(self):
        alarm_logger.info("Monitoring Dime Cluster...")
        while True:
            if self.cluster_status is True:
                for node in self.nodes['dime']:
                    result = self._query_latest_influx(node)
                    for t in self.settings.dime_upper_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) upper threshold for Dime-node: %s", t, result['last_' + t], self.settings.dime_upper_thresholds[t], node)
                        self.check_upper_threshold(
                            result['last_' + t], self.settings.dime_upper_thresholds[t], self.settings.webhooks['dime_scaleup'], t)
                    for t in self.settings.dime_lower_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) lower threshold for Dime-node: %s", t, result['last_' + t], self.settings.dime_lower_thresholds[t], node)
                        self.check_down_threshold(
                            result['last_' + t], self.settings.dime_lower_thresholds[t], self.settings.webhooks['dime_scaledown'], t)
            else:
                alarm_logger.warning(
                    "vIMS Cluster info is updating. Skipping Dime Cluster monitoring...")
            alarm_logger.info(
                "Dime Cluster monitor sleeping for %d seconds...", MONITOR_DELAY)
            time.sleep(MONITOR_DELAY)

    def monitor_vellum(self):
        alarm_logger.info("Monitoring Vellum Cluster...")
        while True:
            if self.cluster_status is True:
                for node in self.nodes['vellum']:
                    result = self._query_latest_influx(node)
                    for t in self.settings.vellum_upper_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) upper threshold for Vellum-node: %s", t, result['last_' + t], self.settings.vellum_upper_thresholds[t], node)
                        self.check_upper_threshold(
                            result['last_' + t], self.settings.vellum_upper_thresholds[t], self.settings.webhooks['vellum_scaleup'], t)
                    for t in self.settings.vellum_lower_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) lower threshold for Vellum-node: %s", t, result['last_' + t], self.settings.vellum_lower_thresholds[t], node)
                        self.check_down_threshold(
                            result['last_' + t], self.settings.vellum_lower_thresholds[t], self.settings.webhooks['vellum_scaledown'], t)
            else:
                alarm_logger.warning(
                    "vIMS Cluster info is updating. Skipping Vellum Cluster monitoring...")
            alarm_logger.info(
                "Vellum Cluster monitor sleeping for %d seconds...", MONITOR_DELAY)
            time.sleep(MONITOR_DELAY)

    def monitor_homer(self):
        alarm_logger.info("Monitoring Homer Cluster...")
        while True:
            if self.cluster_status is True:
                for node in self.nodes['homer']:
                    result = self._query_latest_influx(node)
                    for t in self.settings.homer_upper_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) upper threshold for Homer-node: %s", t, result['last_' + t], self.settings.homer_upper_thresholds[t], node)
                        self.check_upper_threshold(
                            result['last_' + t], self.settings.homer_upper_thresholds[t], self.settings.webhooks['homer_scaleup'], t)
                    for t in self.settings.homer_lower_thresholds.keys():
                        alarm_logger.info(
                            "Checking the '%s' (%s / %s) lower threshold for Homer-node: %s", t, result['last_' + t], self.settings.homer_lower_thresholds[t], node)
                        self.check_down_threshold(
                            result['last_' + t], self.settings.homer_lower_thresholds[t], self.settings.webhooks['homer_scaledown'], t)
            else:
                alarm_logger.warning(
                    "vIMS Cluster info is updating. Skipping Homer Cluster monitoring...")
            alarm_logger.info(
                "Homer Cluster monitor sleeping for %d seconds...", MONITOR_DELAY)
            time.sleep(MONITOR_DELAY)