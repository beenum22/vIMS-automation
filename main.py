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
    logging.config.fileConfig(
        'logging_conf.ini', disable_existing_loggers=False)
    vims_logger = logging.getLogger()
    if args.debug:
        vims_logger.setLevel('DEBUG')
    try:
        vims = vIMS('clearwater-vIMS', 'clearwater-heat/clearwater.yaml', 'clearwater-heat/environment.yaml', args.settings_file)
        vims.setup_env()
        #print vims.nova
        ########################################
        #settings = Settings(args.settings_file)
        # print settings.parse_settings_file()
        #s = Stack(PASSWORD, AUTH_URL)
        #auth = auth = s._authenticate()
        #sess = s._get_session(auth)
        #nova = s._get_novaclient(sess, version='2')
        #neutron = s._get_neutronclient(sess)
        # print nova.servers.list()
        #s.authenticate_clients()
        #print s.find_heat_enpoint('heat')
        #files, temps = s.get_heat_temp_files('clearwater-heat/clearwater.yaml')
        #print files
        #files, temps = s.get_heat_temp_files('test.yaml')

        #params = {'template': temps
        #s.openstack.orchestration.create_stack(name='test_stack', template=temps)
        #s.create_stack('test_stack', 'clearwater-heat/clearwater.yaml')
        #print s.openstack.orchestration.stacks()
        #s.create_stack('test_stack', 'test.yaml')
        # s.create_security_group('ahmad_test')
        # s.allow_ping('ahmad_test')
        #s.open_port('ahmad_test', '443', 'tcp')
        #server = s.create_server('test-3', 'vIMS-key', 'vIMS', 'ubuntu_1404',
        #                ['vIMS-signaling', 'vIMS-management'], ['muneeb_test', 'ahmad_test'])
        #rule = {'dir': 'ingress', 'cidr': '0.0.0.0/0', 'proto': 'icmp',
        #        'port_max': None, 'port_min': None, 'type': 'IPv4'}
        #s.add_security_rule('muneeb_test', rule)
        # print s.upload_image('cirros', url='https://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img')
        # s.get_net_id('Test_vIMS')
        # s.create_net('Test_vIMS')
        #s.create_subnet('test_sub', s.get_net_id('Test_vIMS'), '10.10.0.0/24', '10.10.0.10', pool_size=50)
        # print s.get_net_id('public')
        # print s._get_router(name='clearwater-private-management')
        # print s.neutron.add_interface_router({''=)
        #s.create_router('test_router', ext_gw_net=s.get_net_id('public'))
        #s.add_router_int(s.get_router_id('test_router'), subnet_id=s.get_subnet_id('test_sub'))
        # print json.dumps(s.get_network(name='clearwater-private-signaling'), indent=4, sort_keys=True)
        # print s.create_net('Muneeb')
        #subnet_body['network_id'] = s.get_net_id('Muneeb')
        # print s.get_net_id('Muneeb')
        # print s._get_subnet('public_Sub')
        #s.neutron.create_subnet({'subnet': subnet_body})
        # print Utilities.get_ip_range('10.10.10.0/24', '10.10.10.1', 50)
        # print s.create_subnet('chota_muneeb', s.get_net_id('Muneeb'),
        # '10.10.0.0/24', '10.10.0.1', pool_size=50)

        # print s.neutron.delete_network('Muneeb')
        #outt, err = Utilities._cmd_async(['sudo', 'testing/new.sh'])
        #outt, err = Utilities.run_script('testing/new.sh')
        # if err:
        #    vims_logger.debug(err.strip())
        #    vims_logger.error("Script Execution failed")
        # print "OUTPUT: %s" % outt.strip()
        # print "ERROR: %s" % err.strip()
        #outt, err = Utilities._cmd_async(['testing/test_bash.sh'], pipe_in=subprocess.PIPE)
        # print err
        # Utilities._bash_script('testing/new.sh')
        # print Utilities._cmd_async("grep")
        # print Utilities.run_cmd("/bin/cat settings.ini | grep UNI")[0]
        # print Utilities.run_cmd("ls -la")
        # print u.get_current_directory()
        # print Utilities.get_username()
        # print Utilities._cmd_sync('ping', '-c', '1', '127.0.0.1')
        # if Utilities.ping_host('192.168.10.181'):
        #    vims_logger.info("Host: %s is up", '192.168.10.181')
        # else:
        #    vims_logger.error("Host: %s is down", '192.168.10.181')
        # print Utilities.get_package_path('ping')
        # print Utilities.list_ns()
        # print Utilities.change_os_password('tes', 'test')
        # print Utilities._cmd_sync('cat', 'logging_conf.ini', '|', 'grep', 'formatter')
        # print Utilities._cmd_sync('which', 'p')
        #vims_logger.info("Downloading Ubuntu image...")
        #Utilities.get_file('https://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img', './images', 'cirros.img')
        #vims_logger.info("Download successful")
        #ssh = SshConnection('127.0.0.1', 'ubuntu', 'ubuntu')
        # ssh.open_ssh_connection()
        # ssh.close_ssh_connection()
        ##############################################
    except Exception as err:
        vims_logger.error(err)
        sys.exit("Exiting...")
    except KeyboardInterrupt:
        vims_logger.error("Interrupted. Exiting...")
        sys.exit()

if __name__ == '__main__':
    main()
